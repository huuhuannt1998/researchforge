import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class LiteratureItem(Base):
    __tablename__ = "literature_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    title = Column(String(1000), nullable=False)
    authors = Column(JSONB, nullable=False, default=list)
    year = Column(Integer, nullable=True)
    venue = Column(String(500), nullable=True)
    doi_or_url = Column(String(1000), nullable=True)
    abstract = Column(Text, nullable=True)
    bibtex = Column(Text, nullable=True)
    tags = Column(JSONB, nullable=False, default=list)
    relevance_score = Column(Float, nullable=True)
    pdf_path = Column(String(1000), nullable=True)
    extracted_summary = Column(Text, nullable=True)
    extracted_methods = Column(JSONB, nullable=True)
    extracted_datasets = Column(JSONB, nullable=True)
    extracted_metrics = Column(JSONB, nullable=True)
    extracted_limitations = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    project = relationship("Project", back_populates="literature_items")
    evidence_cards = relationship(
        "EvidenceCard", back_populates="literature_item", cascade="all, delete-orphan"
    )


class EvidenceCard(Base):
    __tablename__ = "evidence_cards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    literature_item_id = Column(
        UUID(as_uuid=True), ForeignKey("literature_items.id", ondelete="SET NULL"), nullable=True
    )
    claim = Column(Text, nullable=False)
    evidence_type = Column(String(100), nullable=True)
    quote_or_paraphrase = Column(Text, nullable=True)
    method = Column(Text, nullable=True)
    metrics = Column(JSONB, nullable=True)
    limitations = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    project = relationship("Project")
    literature_item = relationship("LiteratureItem", back_populates="evidence_cards")
