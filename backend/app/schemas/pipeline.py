from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel


class PipelineRunOut(BaseModel):
    id: UUID
    project_id: UUID
    stage: str
    status: str
    logs: Optional[str] = None
    result_summary: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PipelineRunCreate(BaseModel):
    stage: str
