import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    short_idea = Column(Text, nullable=True)
    problem_statement = Column(Text, nullable=True)
    domain = Column(String(200), nullable=True)
    target_venue = Column(String(200), nullable=True)
    status = Column(String(50), nullable=False, default="draft")
    tags = Column(JSONB, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    research_questions = relationship(
        "ResearchQuestion", back_populates="project", cascade="all, delete-orphan"
    )
    literature_items = relationship(
        "LiteratureItem", back_populates="project", cascade="all, delete-orphan"
    )
    experiment_plans = relationship(
        "ExperimentPlan", back_populates="project", cascade="all, delete-orphan"
    )
    draft_sections = relationship(
        "DraftSection", back_populates="project", cascade="all, delete-orphan"
    )
    review_reports = relationship(
        "ReviewReport", back_populates="project", cascade="all, delete-orphan"
    )


class ResearchQuestion(Base):
    __tablename__ = "research_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    main_question = Column(Text, nullable=False)
    hypotheses = Column(JSONB, nullable=False, default=list)
    assumptions = Column(JSONB, nullable=False, default=list)
    novelty_claim = Column(Text, nullable=True)
    scope_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    project = relationship("Project", back_populates="research_questions")
