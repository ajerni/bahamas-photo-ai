from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.analysis import TripMemoryRead
from backend.app.schemas.photo import PhotoRead
from backend.app.schemas.question import TripQuestionRead


class TripCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=1000)


class TripUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=1000)
    cover_photo_id: int | None = None


class TripRead(BaseModel):
    id: int
    title: str
    description: str | None
    cover_photo_id: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TripDetail(TripRead):
    photos: list[PhotoRead] = Field(default_factory=list)
    memory: TripMemoryRead | None = None
    questions: list[TripQuestionRead] = Field(default_factory=list)
