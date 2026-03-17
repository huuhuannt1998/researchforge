"""
Pipeline router — endpoints to trigger and monitor agent pipeline stages.
"""
from __future__ import annotations

import asyncio
import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import Project
from app.schemas.pipeline import PipelineRunCreate, PipelineRunOut
from app.services import pipeline_service
from app.services.agents import STAGE_RUNNERS

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects/{project_id}/pipeline", tags=["pipeline"])

VALID_STAGES = list(STAGE_RUNNERS.keys())
STAGE_ORDER = ["literature", "design", "code", "evaluation", "writing"]


# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------

def _get_project(db: Session, project_id: UUID) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    return project


def _validate_stage(stage: str) -> None:
    if stage not in VALID_STAGES:
        raise HTTPException(400, f"Invalid stage '{stage}'. Must be one of: {VALID_STAGES}")


# -------------------------------------------------------------------------
# Background task that actually runs an agent stage
# -------------------------------------------------------------------------

async def _run_stage_task(
    project_id: UUID,
    run_id: UUID,
    stage: str,
    db_url: str,
) -> None:
    """Run an agent stage in the background with its own DB session."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(db_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        run_record = pipeline_service.get_run(db, run_id)
        if not run_record:
            log.error("PipelineRun %s not found", run_id)
            return

        runner = STAGE_RUNNERS[stage]
        await runner(db, project_id, run_record)

    except Exception as exc:
        log.exception("Stage %s failed for project %s", stage, project_id)
        run_record = pipeline_service.get_run(db, run_id)
        if run_record and run_record.status != "failed":
            pipeline_service.fail_run(db, run_record, str(exc))
    finally:
        db.close()
        engine.dispose()


def _schedule_stage(
    background_tasks: BackgroundTasks,
    project_id: UUID,
    run_id: UUID,
    stage: str,
    db_url: str,
) -> None:
    """Wrap the async runner in an asyncio task for FastAPI BackgroundTasks."""
    async def _wrapper():
        await _run_stage_task(project_id, run_id, stage, db_url)

    background_tasks.add_task(asyncio.ensure_future, _wrapper())


# -------------------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------------------

@router.get("/", response_model=List[PipelineRunOut])
def list_pipeline_runs(
    project_id: UUID,
    stage: str | None = None,
    db: Session = Depends(get_db),
):
    """List all pipeline runs for a project, optionally filtered by stage."""
    _get_project(db, project_id)
    return pipeline_service.list_runs(db, project_id, stage=stage)


@router.get("/{run_id}", response_model=PipelineRunOut)
def get_pipeline_run(
    project_id: UUID,
    run_id: UUID,
    db: Session = Depends(get_db),
):
    """Get details of a specific pipeline run."""
    _get_project(db, project_id)
    run = pipeline_service.get_run(db, run_id)
    if not run or run.project_id != project_id:
        raise HTTPException(404, "Pipeline run not found")
    return run


@router.post("/{stage}/run", response_model=PipelineRunOut)
async def trigger_stage(
    project_id: UUID,
    stage: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Trigger a single pipeline stage. The stage runs in the background."""
    _get_project(db, project_id)
    _validate_stage(stage)

    # Create the run record
    run = pipeline_service.create_run(db, project_id, stage)

    # Schedule background execution
    from app.config import settings
    background_tasks.add_task(
        _run_stage_in_thread, project_id, run.id, stage, settings.DATABASE_URL
    )

    return run


@router.post("/run-all", response_model=List[PipelineRunOut])
async def trigger_full_pipeline(
    project_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Trigger all stages sequentially (literature → design → code → evaluation → writing)."""
    _get_project(db, project_id)

    runs = []
    for stage in STAGE_ORDER:
        run = pipeline_service.create_run(db, project_id, stage)
        runs.append(run)

    # Schedule the full pipeline in background
    from app.config import settings
    run_ids = [r.id for r in runs]
    background_tasks.add_task(
        _run_full_pipeline_in_thread,
        project_id,
        run_ids,
        settings.DATABASE_URL,
    )

    return runs


# -------------------------------------------------------------------------
# Thread wrappers (BackgroundTasks run in thread pool)
# -------------------------------------------------------------------------

def _run_stage_in_thread(
    project_id: UUID,
    run_id: UUID,
    stage: str,
    db_url: str,
) -> None:
    """Sync wrapper that creates an event loop for the async agent."""
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_run_stage_task(project_id, run_id, stage, db_url))
    finally:
        loop.close()


def _run_full_pipeline_in_thread(
    project_id: UUID,
    run_ids: list[UUID],
    db_url: str,
) -> None:
    """Run all stages sequentially in a background thread."""
    loop = asyncio.new_event_loop()
    try:
        for stage, run_id in zip(STAGE_ORDER, run_ids):
            try:
                loop.run_until_complete(
                    _run_stage_task(project_id, run_id, stage, db_url)
                )
            except Exception:
                log.exception("Full pipeline failed at stage %s", stage)
                break  # Stop pipeline on first failure
    finally:
        loop.close()
