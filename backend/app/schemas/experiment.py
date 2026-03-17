from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class ExperimentPlanBase(BaseModel):
    objective: Optional[str] = None
    hypotheses: List[str] = []
    baselines: List[str] = []
    datasets: List[str] = []
    metrics: List[str] = []
    ablations: List[str] = []
    expected_claims: List[str] = []
    risks: List[str] = []
    compute_notes: Optional[str] = None
    reproducibility_requirements: Optional[str] = None


class ExperimentPlanCreate(ExperimentPlanBase):
    pass


class ExperimentPlanUpdate(BaseModel):
    objective: Optional[str] = None
    hypotheses: Optional[List[str]] = None
    baselines: Optional[List[str]] = None
    datasets: Optional[List[str]] = None
    metrics: Optional[List[str]] = None
    ablations: Optional[List[str]] = None
    expected_claims: Optional[List[str]] = None
    risks: Optional[List[str]] = None
    compute_notes: Optional[str] = None
    reproducibility_requirements: Optional[str] = None


class ExperimentPlanOut(ExperimentPlanBase):
    id: UUID
    project_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
