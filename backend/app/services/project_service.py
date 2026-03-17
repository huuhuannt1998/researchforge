from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.project import Project, ResearchQuestion
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ResearchQuestionCreate,
    ResearchQuestionUpdate,
)


def get_projects(db: Session, skip: int = 0, limit: int = 100) -> List[Project]:
    return (
        db.query(Project)
        .order_by(Project.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_project(db: Session, project_id: UUID) -> Optional[Project]:
    return db.query(Project).filter(Project.id == project_id).first()


def create_project(db: Session, data: ProjectCreate) -> Project:
    project = Project(**data.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def update_project(db: Session, project: Project, data: ProjectUpdate) -> Project:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project: Project) -> None:
    db.delete(project)
    db.commit()


# ---------------------------------------------------------------------------
# Research Questions
# ---------------------------------------------------------------------------

def get_research_question(db: Session, project_id: UUID) -> Optional[ResearchQuestion]:
    return (
        db.query(ResearchQuestion)
        .filter(ResearchQuestion.project_id == project_id)
        .first()
    )


def create_research_question(
    db: Session, project_id: UUID, data: ResearchQuestionCreate
) -> ResearchQuestion:
    rq = ResearchQuestion(project_id=project_id, **data.model_dump())
    db.add(rq)
    db.commit()
    db.refresh(rq)
    return rq


def update_research_question(
    db: Session, rq: ResearchQuestion, data: ResearchQuestionUpdate
) -> ResearchQuestion:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(rq, key, value)
    db.commit()
    db.refresh(rq)
    return rq
