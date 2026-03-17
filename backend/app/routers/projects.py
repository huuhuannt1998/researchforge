from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import ResearchQuestion
from app.schemas.project import (
    ProjectCreate,
    ProjectOut,
    ProjectSummary,
    ProjectUpdate,
    ResearchQuestionCreate,
    ResearchQuestionOut,
    ResearchQuestionUpdate,
)
from app.services import project_service

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("/", response_model=List[ProjectSummary])
def list_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return project_service.get_projects(db, skip=skip, limit=limit)


@router.post("/", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    return project_service.create_project(db, data)


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: UUID, db: Session = Depends(get_db)):
    project = project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(project_id: UUID, data: ProjectUpdate, db: Session = Depends(get_db)):
    project = project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project_service.update_project(db, project, data)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: UUID, db: Session = Depends(get_db)):
    project = project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project_service.delete_project(db, project)


# ---------------------------------------------------------------------------
# Research Question sub-resource (one per project)
# ---------------------------------------------------------------------------

@router.get("/{project_id}/research-question", response_model=ResearchQuestionOut)
def get_research_question(project_id: UUID, db: Session = Depends(get_db)):
    rq = project_service.get_research_question(db, project_id)
    if not rq:
        raise HTTPException(status_code=404, detail="Research question not found")
    return rq


@router.post(
    "/{project_id}/research-question",
    response_model=ResearchQuestionOut,
    status_code=status.HTTP_201_CREATED,
)
def create_research_question(
    project_id: UUID, data: ResearchQuestionCreate, db: Session = Depends(get_db)
):
    project = project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project_service.create_research_question(db, project_id, data)


@router.patch(
    "/{project_id}/research-question/{rq_id}", response_model=ResearchQuestionOut
)
def update_research_question(
    project_id: UUID,
    rq_id: UUID,
    data: ResearchQuestionUpdate,
    db: Session = Depends(get_db),
):
    rq = (
        db.query(ResearchQuestion)
        .filter(ResearchQuestion.id == rq_id, ResearchQuestion.project_id == project_id)
        .first()
    )
    if not rq:
        raise HTTPException(status_code=404, detail="Research question not found")
    return project_service.update_research_question(db, rq, data)
