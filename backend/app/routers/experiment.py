from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.experiment import (
    ExperimentPlanCreate,
    ExperimentPlanOut,
    ExperimentPlanUpdate,
)
from app.services import experiment_service, project_service

router = APIRouter(
    prefix="/api/projects/{project_id}/experiments",
    tags=["experiments"],
)


# ---------------------------------------------------------------------------
# Shared dependency: verify project exists
# ---------------------------------------------------------------------------

def _get_project_or_404(project_id: UUID, db: Session = Depends(get_db)):
    project = project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


# ---------------------------------------------------------------------------
# Experiment plans
# ---------------------------------------------------------------------------

@router.get("/", response_model=List[ExperimentPlanOut])
def list_experiment_plans(
    project_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _project=Depends(_get_project_or_404),
):
    return experiment_service.get_experiment_plans(db, project_id, skip=skip, limit=limit)


@router.post(
    "/",
    response_model=ExperimentPlanOut,
    status_code=status.HTTP_201_CREATED,
)
def create_experiment_plan(
    project_id: UUID,
    data: ExperimentPlanCreate,
    db: Session = Depends(get_db),
    _project=Depends(_get_project_or_404),
):
    return experiment_service.create_experiment_plan(db, project_id, data)


@router.get("/{plan_id}", response_model=ExperimentPlanOut)
def get_experiment_plan(
    project_id: UUID,
    plan_id: UUID,
    db: Session = Depends(get_db),
    _project=Depends(_get_project_or_404),
):
    plan = experiment_service.get_experiment_plan(db, project_id, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Experiment plan not found")
    return plan


@router.patch("/{plan_id}", response_model=ExperimentPlanOut)
def update_experiment_plan(
    project_id: UUID,
    plan_id: UUID,
    data: ExperimentPlanUpdate,
    db: Session = Depends(get_db),
    _project=Depends(_get_project_or_404),
):
    plan = experiment_service.get_experiment_plan(db, project_id, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Experiment plan not found")
    return experiment_service.update_experiment_plan(db, plan, data)


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_experiment_plan(
    project_id: UUID,
    plan_id: UUID,
    db: Session = Depends(get_db),
    _project=Depends(_get_project_or_404),
):
    plan = experiment_service.get_experiment_plan(db, project_id, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Experiment plan not found")
    experiment_service.delete_experiment_plan(db, plan)
