from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AnalysisJobRead(BaseModel):
    id: int
    trip_id: int
    status: str
    current_step: str
    completed_steps: int
    total_steps: int
    mode: str
    error: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
