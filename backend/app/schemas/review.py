from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel

REVIEWER_TYPES = (
    "novelty_critic",
    "evaluation_critic",
    "systems_critic",
    "writing_critic",
    "meta_reviewer",
)


class ReviewReportBase(BaseModel):
    round_name: Optional[str] = None
    reviewer_type: Optional[str] = None
    summary: Optional[str] = None
    scores_json: Optional[Any] = None
    strengths: List[str] = []
    weaknesses: List[str] = []
    missing_experiments: List[str] = []
    unsupported_claims: List[str] = []
    required_fixes: List[str] = []
    optional_suggestions: List[str] = []
    confidence: Optional[float] = None


class ReviewReportCreate(ReviewReportBase):
    pass


class ReviewReportUpdate(BaseModel):
    round_name: Optional[str] = None
    reviewer_type: Optional[str] = None
    summary: Optional[str] = None
    scores_json: Optional[Any] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    missing_experiments: Optional[List[str]] = None
    unsupported_claims: Optional[List[str]] = None
    required_fixes: Optional[List[str]] = None
    optional_suggestions: Optional[List[str]] = None
    confidence: Optional[float] = None


class ReviewReportOut(ReviewReportBase):
    id: UUID
    project_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
