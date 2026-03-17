from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.experiment import ExperimentPlan
from app.schemas.experiment import ExperimentPlanCreate, ExperimentPlanUpdate


def get_experiment_plans(
    db: Session,
    project_id: UUID,
    skip: int = 0,
    limit: int = 100,
) -> List[ExperimentPlan]:
    return (
        db.query(ExperimentPlan)
        .filter(ExperimentPlan.project_id == project_id)
        .order_by(ExperimentPlan.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_experiment_plan(
    db: Session, project_id: UUID, plan_id: UUID
) -> Optional[ExperimentPlan]:
    return (
        db.query(ExperimentPlan)
        .filter(
            ExperimentPlan.id == plan_id,
            ExperimentPlan.project_id == project_id,
        )
        .first()
    )


def create_experiment_plan(
    db: Session, project_id: UUID, data: ExperimentPlanCreate
) -> ExperimentPlan:
    plan = ExperimentPlan(project_id=project_id, **data.model_dump())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def update_experiment_plan(
    db: Session, plan: ExperimentPlan, data: ExperimentPlanUpdate
) -> ExperimentPlan:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(plan, key, value)
    db.commit()
    db.refresh(plan)
    return plan


def delete_experiment_plan(db: Session, plan: ExperimentPlan) -> None:
    db.delete(plan)
    db.commit()
