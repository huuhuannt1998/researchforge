"""Agent modules — autonomous research pipeline stages."""
from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.pipeline import PipelineRun


# -------------------------------------------------------------------------
# Shared helpers used by individual agent modules
# -------------------------------------------------------------------------

def _get_latest_run_result(db: Session, project_id: UUID, stage: str) -> Optional[str]:
    """Return the result_summary of the most recent *completed* run for a stage."""
    run = (
        db.query(PipelineRun)
        .filter(
            PipelineRun.project_id == project_id,
            PipelineRun.stage == stage,
            PipelineRun.status == "completed",
        )
        .order_by(PipelineRun.completed_at.desc())
        .first()
    )
    return run.result_summary if run else None


def _get_latest_run_data(db: Session, project_id: UUID, stage: str) -> Optional[Dict[str, Any]]:
    """Return the result_data JSON of the most recent *completed* run for a stage."""
    run = (
        db.query(PipelineRun)
        .filter(
            PipelineRun.project_id == project_id,
            PipelineRun.stage == stage,
            PipelineRun.status == "completed",
        )
        .order_by(PipelineRun.completed_at.desc())
        .first()
    )
    return run.result_data if run else None


# -------------------------------------------------------------------------
# Stage runners (lazy imports to avoid circular deps)
# -------------------------------------------------------------------------

from app.services.agents.literature_agent import run as run_literature  # noqa: E402
from app.services.agents.design_agent import run as run_design  # noqa: E402
from app.services.agents.code_agent import run as run_code  # noqa: E402
from app.services.agents.evaluation_agent import run as run_evaluation  # noqa: E402
from app.services.agents.writing_agent import run as run_writing  # noqa: E402

STAGE_RUNNERS = {
    "literature": run_literature,
    "design": run_design,
    "code": run_code,
    "evaluation": run_evaluation,
    "writing": run_writing,
}

__all__ = [
    "STAGE_RUNNERS",
    "_get_latest_run_result",
    "_get_latest_run_data",
    "run_literature",
    "run_design",
    "run_code",
    "run_evaluation",
    "run_writing",
]
