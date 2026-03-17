from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# ResearchQuestion
# ---------------------------------------------------------------------------

class ResearchQuestionBase(BaseModel):
    main_question: str
    hypotheses: List[str] = []
    assumptions: List[str] = []
    novelty_claim: Optional[str] = None
    scope_notes: Optional[str] = None


class ResearchQuestionCreate(ResearchQuestionBase):
    pass


class ResearchQuestionUpdate(BaseModel):
    main_question: Optional[str] = None
    hypotheses: Optional[List[str]] = None
    assumptions: Optional[List[str]] = None
    novelty_claim: Optional[str] = None
    scope_notes: Optional[str] = None


class ResearchQuestionOut(ResearchQuestionBase):
    id: UUID
    project_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------

PROJECT_STATUSES = ("draft", "active", "submitted", "published", "archived")


class ProjectBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    short_idea: Optional[str] = None
    problem_statement: Optional[str] = None
    domain: Optional[str] = None
    target_venue: Optional[str] = None
    status: str = "draft"
    tags: List[str] = []


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    short_idea: Optional[str] = None
    problem_statement: Optional[str] = None
    domain: Optional[str] = None
    target_venue: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None


class ProjectOut(ProjectBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    research_questions: List[ResearchQuestionOut] = []

    model_config = {"from_attributes": True}


class ProjectSummary(BaseModel):
    """Lightweight project record for dashboard listing."""

    id: UUID
    title: str
    short_idea: Optional[str] = None
    domain: Optional[str] = None
    target_venue: Optional[str] = None
    status: str
    tags: List[str] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
