import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    # Stage: literature, design, code, evaluation, writing
    stage = Column(String(50), nullable=False)
    # Status: pending, running, completed, failed
    status = Column(String(50), nullable=False, default="pending")
    # Logs accumulated during the run
    logs = Column(Text, nullable=True)
    # Structured result data
    result_summary = Column(Text, nullable=True)
    result_data = Column(JSONB, nullable=True)
    # Error message if failed
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    project = relationship("Project", back_populates="pipeline_runs")
