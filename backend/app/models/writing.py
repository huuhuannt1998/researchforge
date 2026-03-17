import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class DraftSection(Base):
    __tablename__ = "draft_sections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    # e.g. "abstract", "introduction", "related_work", "methodology", "experiments",
    #      "results", "discussion", "conclusion", "appendix"
    section_key = Column(String(100), nullable=False)
    title = Column(String(500), nullable=False)
    content_markdown = Column(Text, nullable=True)
    content_latex = Column(Text, nullable=True)
    linked_evidence_ids = Column(JSONB, nullable=False, default=list)
    linked_run_ids = Column(JSONB, nullable=False, default=list)
    revision_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    project = relationship("Project", back_populates="draft_sections")
