from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel


class LiteratureItemBase(BaseModel):
    title: str
    authors: List[str] = []
    year: Optional[int] = None
    venue: Optional[str] = None
    doi_or_url: Optional[str] = None
    abstract: Optional[str] = None
    bibtex: Optional[str] = None
    tags: List[str] = []
    relevance_score: Optional[float] = None


class LiteratureItemCreate(LiteratureItemBase):
    pass


class LiteratureItemUpdate(BaseModel):
    title: Optional[str] = None
    authors: Optional[List[str]] = None
    year: Optional[int] = None
    venue: Optional[str] = None
    doi_or_url: Optional[str] = None
    abstract: Optional[str] = None
    bibtex: Optional[str] = None
    tags: Optional[List[str]] = None
    relevance_score: Optional[float] = None
    extracted_summary: Optional[str] = None
    extracted_methods: Optional[Any] = None
    extracted_datasets: Optional[Any] = None
    extracted_metrics: Optional[Any] = None
    extracted_limitations: Optional[Any] = None


class LiteratureItemOut(LiteratureItemBase):
    id: UUID
    project_id: UUID
    pdf_path: Optional[str] = None
    extracted_summary: Optional[str] = None
    extracted_methods: Optional[Any] = None
    extracted_datasets: Optional[Any] = None
    extracted_metrics: Optional[Any] = None
    extracted_limitations: Optional[Any] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# EvidenceCard
# ---------------------------------------------------------------------------

class EvidenceCardBase(BaseModel):
    claim: str
    evidence_type: Optional[str] = None
    quote_or_paraphrase: Optional[str] = None
    method: Optional[str] = None
    metrics: Optional[Any] = None
    limitations: Optional[str] = None
    notes: Optional[str] = None
    confidence: Optional[float] = None


class EvidenceCardCreate(EvidenceCardBase):
    literature_item_id: Optional[UUID] = None


class EvidenceCardUpdate(BaseModel):
    claim: Optional[str] = None
    evidence_type: Optional[str] = None
    quote_or_paraphrase: Optional[str] = None
    method: Optional[str] = None
    metrics: Optional[Any] = None
    limitations: Optional[str] = None
    notes: Optional[str] = None
    confidence: Optional[float] = None


class EvidenceCardOut(EvidenceCardBase):
    id: UUID
    project_id: UUID
    literature_item_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
