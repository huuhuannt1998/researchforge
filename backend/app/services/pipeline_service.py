"""
Pipeline service — CRUD operations for PipelineRun records.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.pipeline import PipelineRun


def list_runs(
    db: Session, project_id: UUID, *, stage: str | None = None
) -> List[PipelineRun]:
    q = db.query(PipelineRun).filter(PipelineRun.project_id == project_id)
    if stage:
        q = q.filter(PipelineRun.stage == stage)
    return q.order_by(PipelineRun.created_at.desc()).all()


def get_run(db: Session, run_id: UUID) -> Optional[PipelineRun]:
    return db.query(PipelineRun).filter(PipelineRun.id == run_id).first()


def create_run(db: Session, project_id: UUID, stage: str) -> PipelineRun:
    run = PipelineRun(
        project_id=project_id,
        stage=stage,
        status="pending",
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def start_run(db: Session, run: PipelineRun) -> PipelineRun:
    run.status = "running"
    run.started_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(run)
    return run


def complete_run(
    db: Session,
    run: PipelineRun,
    *,
    result_summary: str | None = None,
    result_data: dict | None = None,
    logs: str | None = None,
) -> PipelineRun:
    run.status = "completed"
    run.completed_at = datetime.now(timezone.utc)
    if result_summary is not None:
        run.result_summary = result_summary
    if result_data is not None:
        run.result_data = result_data
    if logs is not None:
        run.logs = logs
    db.commit()
    db.refresh(run)
    return run


def fail_run(
    db: Session,
    run: PipelineRun,
    error_message: str,
    logs: str | None = None,
) -> PipelineRun:
    run.status = "failed"
    run.completed_at = datetime.now(timezone.utc)
    run.error_message = error_message
    if logs is not None:
        run.logs = logs
    db.commit()
    db.refresh(run)
    return run


def append_log(db: Session, run: PipelineRun, line: str) -> None:
    """Append a line to the run's log buffer."""
    if run.logs:
        run.logs += "\n" + line
    else:
        run.logs = line
    db.commit()
