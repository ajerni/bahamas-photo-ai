from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TripQuestionRead(BaseModel):
    id: int
    trip_id: int
    question: str
    answer: str
    evidence_photo_ids: list[int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
