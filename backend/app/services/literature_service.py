from __future__ import annotations

import shutil
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.config import settings
from app.models.literature import EvidenceCard, LiteratureItem
from app.schemas.literature import (
    EvidenceCardCreate,
    EvidenceCardUpdate,
    LiteratureItemCreate,
    LiteratureItemUpdate,
)
from app.services.extraction_service import extract_from_pdf, extract_from_url


# ---------------------------------------------------------------------------
# LiteratureItem helpers
# ---------------------------------------------------------------------------

def get_literature_items(
    db: Session, project_id: UUID, skip: int = 0, limit: int = 200
) -> List[LiteratureItem]:
    return (
        db.query(LiteratureItem)
        .filter(LiteratureItem.project_id == project_id)
        .order_by(LiteratureItem.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_literature_item(
    db: Session, project_id: UUID, item_id: UUID
) -> Optional[LiteratureItem]:
    return (
        db.query(LiteratureItem)
        .filter(
            LiteratureItem.id == item_id,
            LiteratureItem.project_id == project_id,
        )
        .first()
    )


def create_literature_item(
    db: Session, project_id: UUID, data: LiteratureItemCreate
) -> LiteratureItem:
    item = LiteratureItem(project_id=project_id, **data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_literature_item(
    db: Session, item: LiteratureItem, data: LiteratureItemUpdate
) -> LiteratureItem:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


def delete_literature_item(db: Session, item: LiteratureItem) -> None:
    # Remove PDF file if stored locally
    if item.pdf_path:
        try:
            Path(item.pdf_path).unlink(missing_ok=True)
        except Exception:
            pass
    db.delete(item)
    db.commit()


# ---------------------------------------------------------------------------
# PDF upload + extraction
# ---------------------------------------------------------------------------

def _project_storage_dir(project_id: UUID) -> Path:
    base = Path(settings.STORAGE_BASE_PATH)
    d = base / str(project_id) / "literature"
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_pdf(project_id: UUID, filename: str, content: bytes) -> str:
    """Persist uploaded PDF bytes to project storage; return absolute path."""
    dest = _project_storage_dir(project_id) / filename
    dest.write_bytes(content)
    return str(dest)


def run_extraction_on_item(db: Session, item: LiteratureItem) -> LiteratureItem:
    """
    Trigger extraction on an existing LiteratureItem.

    Uses pdf_path if available, otherwise falls back to doi_or_url.
    Stores results back to the DB record.
    """
    result = None
    if item.pdf_path:
        result = extract_from_pdf(item.pdf_path)
    elif item.doi_or_url:
        result = extract_from_url(item.doi_or_url)

    if result is None:
        return item  # nothing to extract from

    item.extracted_summary = result.summary
    item.extracted_methods = result.methods
    item.extracted_datasets = result.datasets
    item.extracted_metrics = result.metrics
    item.extracted_limitations = result.limitations
    db.commit()
    db.refresh(item)
    return item


# ---------------------------------------------------------------------------
# EvidenceCard helpers
# ---------------------------------------------------------------------------

def get_evidence_cards(
    db: Session,
    project_id: UUID,
    literature_item_id: Optional[UUID] = None,
) -> List[EvidenceCard]:
    q = db.query(EvidenceCard).filter(EvidenceCard.project_id == project_id)
    if literature_item_id is not None:
        q = q.filter(EvidenceCard.literature_item_id == literature_item_id)
    return q.order_by(EvidenceCard.created_at.desc()).all()


def get_evidence_card(
    db: Session, project_id: UUID, card_id: UUID
) -> Optional[EvidenceCard]:
    return (
        db.query(EvidenceCard)
        .filter(
            EvidenceCard.id == card_id,
            EvidenceCard.project_id == project_id,
        )
        .first()
    )


def create_evidence_card(
    db: Session, project_id: UUID, data: EvidenceCardCreate
) -> EvidenceCard:
    card = EvidenceCard(project_id=project_id, **data.model_dump())
    db.add(card)
    db.commit()
    db.refresh(card)
    return card


def update_evidence_card(
    db: Session, card: EvidenceCard, data: EvidenceCardUpdate
) -> EvidenceCard:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(card, key, value)
    db.commit()
    db.refresh(card)
    return card


def delete_evidence_card(db: Session, card: EvidenceCard) -> None:
    db.delete(card)
    db.commit()
