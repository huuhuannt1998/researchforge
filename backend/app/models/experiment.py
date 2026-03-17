import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ExperimentPlan(Base):
    __tablename__ = "experiment_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    objective = Column(Text, nullable=True)
    hypotheses = Column(JSONB, nullable=False, default=list)
    baselines = Column(JSONB, nullable=False, default=list)
    datasets = Column(JSONB, nullable=False, default=list)
    metrics = Column(JSONB, nullable=False, default=list)
    ablations = Column(JSONB, nullable=False, default=list)
    expected_claims = Column(JSONB, nullable=False, default=list)
    risks = Column(JSONB, nullable=False, default=list)
    compute_notes = Column(Text, nullable=True)
    reproducibility_requirements = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    project = relationship("Project", back_populates="experiment_plans")
