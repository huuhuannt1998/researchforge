"""
Design Agent
=============
Takes the literature review output and research question, then uses the LLM
to propose a complete experiment design — hypotheses, baselines, datasets,
metrics, ablations, risks — and stores it as an ExperimentPlan.
"""
from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.experiment import ExperimentPlan
from app.models.literature import LiteratureItem
from app.models.pipeline import PipelineRun
from app.models.project import Project, ResearchQuestion
from app.services import llm_service, pipeline_service

log = logging.getLogger(__name__)

DESIGN_SYSTEM = """\
You are an expert research scientist designing an experiment plan.

Given a research topic, research question, and a literature review synthesis,
produce a detailed experiment design as a JSON object:

{
  "objective": "Clear 1-2 sentence objective",
  "hypotheses": ["H1: ...", "H2: ..."],
  "baselines": ["Baseline method 1", "Baseline method 2"],
  "datasets": ["Dataset1", "Dataset2"],
  "metrics": ["Metric1", "Metric2"],
  "ablations": ["Ablation study 1"],
  "expected_claims": ["Claim we expect to make 1"],
  "risks": ["Risk / potential blocker 1"],
  "compute_notes": "Estimated compute requirements",
  "reproducibility_requirements": "Steps to ensure reproducibility"
}

Be specific and grounded in the literature. Propose realistic experiments
that a single researcher could execute.
"""


async def run(db: Session, project_id: UUID, run_record: PipelineRun) -> None:
    """Generate an experiment design from literature analysis."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError(f"Project {project_id} not found")

    pipeline_service.start_run(db, run_record)
    pipeline_service.append_log(db, run_record, "🔬 Design agent started")

    # Gather context
    topic = project.short_idea or project.title
    rq = (
        db.query(ResearchQuestion)
        .filter(ResearchQuestion.project_id == project_id)
        .first()
    )
    question_text = rq.main_question if rq else ""

    # Get literature synthesis from the most recent literature run
    from app.services.agents import _get_latest_run_result
    lit_synthesis = _get_latest_run_result(db, project_id, "literature")

    # Also gather paper summaries
    lit_items = (
        db.query(LiteratureItem)
        .filter(LiteratureItem.project_id == project_id)
        .all()
    )
    paper_summaries = "\n".join(
        f"- {item.title}: {item.extracted_summary or 'No summary'}"
        for item in lit_items[:15]
    )

    pipeline_service.append_log(db, run_record, "🧠 Asking LLM to design experiments…")

    design = await llm_service.chat_json([
        {"role": "system", "content": DESIGN_SYSTEM},
        {"role": "user", "content": (
            f"Research topic: {topic}\n"
            f"Research question: {question_text}\n\n"
            f"Literature review:\n{lit_synthesis or 'No literature review available yet.'}\n\n"
            f"Key papers:\n{paper_summaries}"
        )},
    ], max_tokens=4096)

    # Upsert ExperimentPlan
    existing = (
        db.query(ExperimentPlan)
        .filter(ExperimentPlan.project_id == project_id)
        .first()
    )
    fields = {
        "objective": design.get("objective", ""),
        "hypotheses": design.get("hypotheses", []),
        "baselines": design.get("baselines", []),
        "datasets": design.get("datasets", []),
        "metrics": design.get("metrics", []),
        "ablations": design.get("ablations", []),
        "expected_claims": design.get("expected_claims", []),
        "risks": design.get("risks", []),
        "compute_notes": design.get("compute_notes", ""),
        "reproducibility_requirements": design.get("reproducibility_requirements", ""),
    }
    if existing:
        for k, v in fields.items():
            setattr(existing, k, v)
    else:
        plan = ExperimentPlan(project_id=project_id, **fields)
        db.add(plan)
    db.commit()

    pipeline_service.complete_run(
        db, run_record,
        result_summary=f"Experiment plan created: {design.get('objective', '')[:200]}",
        result_data=design,
    )
    pipeline_service.append_log(db, run_record, "✅ Experiment design complete")
