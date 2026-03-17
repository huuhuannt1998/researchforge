import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ReviewReport(Base):
    __tablename__ = "review_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    round_name = Column(String(200), nullable=True)
    # One of: novelty_critic, evaluation_critic, systems_critic, writing_critic, meta_reviewer
    reviewer_type = Column(String(100), nullable=True)
    summary = Column(Text, nullable=True)
    scores_json = Column(JSONB, nullable=True)
    strengths = Column(JSONB, nullable=False, default=list)
    weaknesses = Column(JSONB, nullable=False, default=list)
    missing_experiments = Column(JSONB, nullable=False, default=list)
    unsupported_claims = Column(JSONB, nullable=False, default=list)
    required_fixes = Column(JSONB, nullable=False, default=list)
    optional_suggestions = Column(JSONB, nullable=False, default=list)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    project = relationship("Project", back_populates="review_reports")
