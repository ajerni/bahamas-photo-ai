from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PhotoMemoryAnalysis(BaseModel):
    scene_summary: str = Field(min_length=1, max_length=500)
    memory_caption: str = Field(min_length=1, max_length=240)
    place_type: str = Field(min_length=1, max_length=120)
    visible_activities: list[str] = Field(default_factory=list, max_length=12)
    visible_objects: list[str] = Field(default_factory=list, max_length=20)
    sensory_details: list[str] = Field(default_factory=list, max_length=12)
    inferred_interest_signals: list[str] = Field(default_factory=list, max_length=12)
    mood: str = Field(min_length=1, max_length=120)
    uncertainty_notes: list[str] = Field(default_factory=list, max_length=8)
    confidence: float = Field(ge=0.0, le=1.0)


class MemorableMoment(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=500)
    evidence_photo_ids: list[int] = Field(default_factory=list, min_length=1)


class TripMemorySynthesis(BaseModel):
    narrative_summary: str = Field(min_length=1, max_length=2500)
    inferred_interests: list[str] = Field(default_factory=list, max_length=16)
    recurring_themes: list[str] = Field(default_factory=list, max_length=16)
    memorable_moments: list[MemorableMoment] = Field(default_factory=list, max_length=20)
    evidence_photo_ids: list[int] = Field(default_factory=list, min_length=1)
    uncertainty_notes: list[str] = Field(default_factory=list, max_length=10)


class GroundedTripAnswer(BaseModel):
    answer: str = Field(min_length=1, max_length=2000)
    evidence_photo_ids: list[int] = Field(default_factory=list)
    uncertainty: str = Field(default="", max_length=500)


class TripWorkflowResult(BaseModel):
    trip_id: int
    analyzed_photo_ids: list[int]
    trip_memory_created: bool
    prompt_version: str
    qa_ready: bool


class PhotoContext(BaseModel):
    id: int
    filename: str
    captured_at: str | None
    latitude: float | None
    longitude: float | None
    exif_json: dict[str, Any]


class AnalyzedPhotoContext(PhotoContext):
    analysis: PhotoMemoryAnalysis
