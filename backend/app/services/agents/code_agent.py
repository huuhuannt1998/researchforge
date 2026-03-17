"""
Code Agent
==========
Takes the experiment plan and generates Python code to run the experiments.
Writes the code to the project workspace, executes it, and captures output.
"""
from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from app.config import settings
from app.models.experiment import ExperimentPlan
from app.models.pipeline import PipelineRun
from app.models.project import Project
from app.services import llm_service, pipeline_service

log = logging.getLogger(__name__)

CODE_GEN_SYSTEM = """\
You are an expert ML/research engineer. Given an experiment plan, generate
a complete, self-contained Python script that implements the experiments.

Requirements:
- The script should be runnable with `python experiment.py`
- Use common libraries (numpy, scikit-learn, pandas, matplotlib) when possible
- Include data loading/generation, model training/evaluation, and result reporting
- Print all results to stdout in a structured format
- Save any plots to the current working directory
- Include proper error handling
- Add comments explaining each section

Return ONLY the Python code, no markdown fences or explanations.
"""

CODE_FIX_SYSTEM = """\
You are an expert Python debugger. The following code produced an error.
Fix the code and return ONLY the corrected Python code, no explanations.
"""


def _project_code_dir(project_id: UUID) -> Path:
    """Return (and create) the code workspace directory for a project."""
    d = Path(settings.STORAGE_BASE_PATH) / str(project_id) / "code"
    d.mkdir(parents=True, exist_ok=True)
    return d


async def run(db: Session, project_id: UUID, run_record: PipelineRun) -> None:
    """Generate experiment code, execute it, and capture results."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError(f"Project {project_id} not found")

    pipeline_service.start_run(db, run_record)
    pipeline_service.append_log(db, run_record, "💻 Code agent started")

    # Gather experiment plan
    plan = (
        db.query(ExperimentPlan)
        .filter(ExperimentPlan.project_id == project_id)
        .first()
    )
    if not plan:
        pipeline_service.fail_run(
            db, run_record,
            "No experiment plan found. Run the Design stage first.",
        )
        return

    plan_text = (
        f"Objective: {plan.objective}\n"
        f"Hypotheses: {plan.hypotheses}\n"
        f"Baselines: {plan.baselines}\n"
        f"Datasets: {plan.datasets}\n"
        f"Metrics: {plan.metrics}\n"
        f"Ablations: {plan.ablations}\n"
        f"Compute notes: {plan.compute_notes}"
    )

    # Step 1 — Generate code
    pipeline_service.append_log(db, run_record, "🧠 Generating experiment code…")
    code = await llm_service.chat([
        {"role": "system", "content": CODE_GEN_SYSTEM},
        {"role": "user", "content": f"Experiment plan:\n{plan_text}"},
    ], temperature=0.3, max_tokens=8192)

    # Clean markdown fences if present
    if code.startswith("```"):
        lines = code.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        code = "\n".join(lines)

    # Save to workspace
    code_dir = _project_code_dir(project_id)
    script_path = code_dir / "experiment.py"
    script_path.write_text(code, encoding="utf-8")
    pipeline_service.append_log(db, run_record, f"   Saved to {script_path}")

    # Step 2 — Execute code (with retry on failure)
    max_attempts = 2
    stdout_text = ""
    stderr_text = ""

    for attempt in range(1, max_attempts + 1):
        pipeline_service.append_log(
            db, run_record, f"🚀 Executing experiment (attempt {attempt})…"
        )
        stdout_text, stderr_text, returncode = await _execute_script(script_path)

        if returncode == 0:
            pipeline_service.append_log(db, run_record, "   Execution succeeded")
            break

        pipeline_service.append_log(
            db, run_record,
            f"   ⚠ Execution failed (code {returncode}). Stderr:\n{stderr_text[:500]}"
        )

        if attempt < max_attempts:
            # Try to fix the code
            pipeline_service.append_log(db, run_record, "🔧 Asking LLM to fix the code…")
            fixed_code = await llm_service.chat([
                {"role": "system", "content": CODE_FIX_SYSTEM},
                {"role": "user", "content": (
                    f"Code:\n```python\n{code}\n```\n\n"
                    f"Error:\n{stderr_text[:2000]}"
                )},
            ], temperature=0.2, max_tokens=8192)
            # Clean markdown fences
            if fixed_code.startswith("```"):
                flines = fixed_code.split("\n")
                flines = [l for l in flines if not l.strip().startswith("```")]
                fixed_code = "\n".join(flines)
            code = fixed_code
            script_path.write_text(code, encoding="utf-8")

    # Step 3 — Store results
    results_data = {
        "script_path": str(script_path),
        "stdout": stdout_text[:10000],
        "stderr": stderr_text[:5000],
        "returncode": returncode,
        "attempts": attempt,
    }

    # List any output files
    output_files = [
        str(f.relative_to(code_dir))
        for f in code_dir.iterdir()
        if f.name != "experiment.py"
    ]
    results_data["output_files"] = output_files

    if returncode == 0:
        pipeline_service.complete_run(
            db, run_record,
            result_summary=f"Code executed successfully. Output files: {output_files}",
            result_data=results_data,
        )
        pipeline_service.append_log(db, run_record, "✅ Code generation & execution complete")
    else:
        pipeline_service.fail_run(
            db, run_record,
            f"Code execution failed after {max_attempts} attempts",
            logs=run_record.logs,
        )


async def _execute_script(script_path: Path) -> tuple[str, str, int]:
    """Run a Python script as a subprocess and return (stdout, stderr, returncode)."""
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    proc = await asyncio.create_subprocess_exec(
        "python3", str(script_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(script_path.parent),
        env=env,
    )
    try:
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(), timeout=300  # 5 min timeout
        )
    except asyncio.TimeoutError:
        proc.kill()
        return "", "Execution timed out after 300 seconds", -1

    return (
        stdout_bytes.decode("utf-8", errors="replace"),
        stderr_bytes.decode("utf-8", errors="replace"),
        proc.returncode or 0,
    )
