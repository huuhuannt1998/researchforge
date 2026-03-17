from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

SECTION_KEYS = [
    "abstract",
    "introduction",
    "related_work",
    "methodology",
    "experiments",
    "results",
    "discussion",
    "conclusion",
    "appendix",
]


class DraftSectionBase(BaseModel):
    section_key: str
    title: str
    content_markdown: Optional[str] = None
    content_latex: Optional[str] = None
    linked_evidence_ids: List[str] = []
    linked_run_ids: List[str] = []
    revision_note: Optional[str] = None


class DraftSectionCreate(DraftSectionBase):
    pass


class DraftSectionUpdate(BaseModel):
    section_key: Optional[str] = None
    title: Optional[str] = None
    content_markdown: Optional[str] = None
    content_latex: Optional[str] = None
    linked_evidence_ids: Optional[List[str]] = None
    linked_run_ids: Optional[List[str]] = None
    revision_note: Optional[str] = None


class DraftSectionOut(DraftSectionBase):
    id: UUID
    project_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
