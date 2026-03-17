"""
Evaluation Agent
================
Takes code execution output and uses the LLM to:
1. Parse and structure experimental results into tables.
2. Compare against baselines.
3. Identify statistically significant findings.
4. Generate figure/table descriptions.
"""
from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.pipeline import PipelineRun
from app.models.project import Project
from app.services import llm_service, pipeline_service

log = logging.getLogger(__name__)

EVALUATION_SYSTEM = """\
You are an expert research scientist evaluating experimental results.

Given the experiment plan and the raw output from running the experiments,
produce a comprehensive evaluation as a JSON object:

{
  "results_table": [
    {"method": "...", "metric1": 0.95, "metric2": 0.87}
  ],
  "best_method": "Name of the best-performing method",
  "key_findings": ["Finding 1", "Finding 2"],
  "hypothesis_verdicts": [
    {"hypothesis": "H1: ...", "supported": true, "evidence": "..."}
  ],
  "ablation_results": [
    {"ablation": "Without X", "effect": "Performance dropped by Y%"}
  ],
  "figure_suggestions": [
    {"type": "bar_chart", "title": "...", "description": "..."}
  ],
  "limitations_observed": ["Limitation 1"],
  "overall_summary": "2-3 sentence summary of the evaluation"
}

Be rigorous and honest. If results are inconclusive, say so.
"""


async def run(db: Session, project_id: UUID, run_record: PipelineRun) -> None:
    """Analyze experiment results and produce structured evaluation."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError(f"Project {project_id} not found")

    pipeline_service.start_run(db, run_record)
    pipeline_service.append_log(db, run_record, "📊 Evaluation agent started")

    # Get experiment plan context
    from app.models.experiment import ExperimentPlan
    plan = (
        db.query(ExperimentPlan)
        .filter(ExperimentPlan.project_id == project_id)
        .first()
    )
    plan_text = ""
    if plan:
        plan_text = (
            f"Objective: {plan.objective}\n"
            f"Hypotheses: {plan.hypotheses}\n"
            f"Metrics: {plan.metrics}\n"
            f"Baselines: {plan.baselines}\n"
            f"Ablations: {plan.ablations}"
        )

    # Get code execution output from latest code run
    from app.services.agents import _get_latest_run_data
    code_data = _get_latest_run_data(db, project_id, "code")
    if not code_data:
        pipeline_service.fail_run(
            db, run_record,
            "No code execution results found. Run the Code stage first.",
        )
        return

    stdout = code_data.get("stdout", "No output")
    stderr = code_data.get("stderr", "")
    output_files = code_data.get("output_files", [])

    pipeline_service.append_log(db, run_record, "🧠 Analyzing results with LLM…")

    evaluation = await llm_service.chat_json([
        {"role": "system", "content": EVALUATION_SYSTEM},
        {"role": "user", "content": (
            f"Experiment plan:\n{plan_text}\n\n"
            f"Code output (stdout):\n{stdout[:8000]}\n\n"
            f"Errors (stderr):\n{stderr[:2000]}\n\n"
            f"Output files: {output_files}"
        )},
    ], max_tokens=4096)

    summary = evaluation.get("overall_summary", "Evaluation complete.")
    pipeline_service.complete_run(
        db, run_record,
        result_summary=summary,
        result_data=evaluation,
    )
    pipeline_service.append_log(db, run_record, "✅ Evaluation complete")
