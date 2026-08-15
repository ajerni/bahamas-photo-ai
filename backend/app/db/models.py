from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import Column, JSON
from sqlmodel import Field, Relationship, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Trip(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(index=True, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=1000)
    cover_photo_id: int | None = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=utc_now, index=True)

    photos: list["Photo"] = Relationship(back_populates="trip")
    memory: Optional["TripMemory"] = Relationship(back_populates="trip")
    jobs: list["AnalysisJob"] = Relationship(back_populates="trip")


class Photo(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    trip_id: int = Field(foreign_key="trip.id", index=True)
    filename: str = Field(max_length=255)
    stored_path: str = Field(index=True, max_length=500)
    content_sha256: str | None = Field(default=None, index=True, max_length=64)
    byte_size: int | None = Field(default=None, ge=0)
    mime_type: str | None = Field(default=None, max_length=120)
    captured_at: datetime | None = Field(default=None, index=True)
    latitude: float | None = Field(default=None, index=True)
    longitude: float | None = Field(default=None, index=True)
    exif_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    is_favorite: bool = Field(default=False, index=True)
    created_at: datetime = Field(default_factory=utc_now, index=True)

    trip: Trip | None = Relationship(back_populates="photos")
    analysis: Optional["PhotoAnalysis"] = Relationship(back_populates="photo")


class PhotoAnalysis(SQLModel, table=True):
    photo_id: int = Field(foreign_key="photo.id", primary_key=True)
    scene: str = Field(default="", max_length=500)
    activities: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    objects: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    mood: str = Field(default="", max_length=160)
    memory_prompt: str = Field(default="", max_length=1000)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    raw_model_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    user_memory_caption: str | None = Field(default=None, max_length=1000)
    user_scene_summary: str | None = Field(default=None, max_length=500)
    user_mood: str | None = Field(default=None, max_length=160)
    user_note: str | None = Field(default=None, max_length=2000)
    updated_at: datetime = Field(default_factory=utc_now)

    photo: Photo | None = Relationship(back_populates="analysis")

    @property
    def photo_memory(self) -> dict[str, Any]:
        value = self.raw_model_json.get("photo_memory")
        return value if isinstance(value, dict) else {}

    @property
    def scene_summary(self) -> str:
        return str(self.user_scene_summary or self.photo_memory.get("scene_summary") or self.scene)

    @property
    def memory_caption(self) -> str:
        return str(self.user_memory_caption or self.photo_memory.get("memory_caption") or self.memory_prompt)

    @property
    def place_type(self) -> str:
        return str(self.photo_memory.get("place_type") or "")

    @property
    def visible_activities(self) -> list[str]:
        return _string_list(self.photo_memory.get("visible_activities") or self.activities)

    @property
    def visible_objects(self) -> list[str]:
        return _string_list(self.photo_memory.get("visible_objects") or self.objects)

    @property
    def sensory_details(self) -> list[str]:
        return _string_list(self.photo_memory.get("sensory_details"))

    @property
    def inferred_interest_signals(self) -> list[str]:
        return _string_list(self.photo_memory.get("inferred_interest_signals"))

    @property
    def uncertainty_notes(self) -> list[str]:
        return _string_list(self.photo_memory.get("uncertainty_notes"))


class TripMemory(SQLModel, table=True):
    trip_id: int = Field(foreign_key="trip.id", primary_key=True)
    narrative_summary: str = Field(default="", max_length=2500)
    inferred_interests: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    recurring_themes: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    memorable_moments: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    evidence_photo_ids: list[int] = Field(default_factory=list, sa_column=Column(JSON))
    uncertainty_notes: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    raw_model_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    user_narrative_summary: str | None = Field(default=None, max_length=2500)
    user_note: str | None = Field(default=None, max_length=2000)
    prompt_version: str = Field(default="travel-memory-v1", max_length=80, index=True)
    created_at: datetime = Field(default_factory=utc_now, index=True)
    updated_at: datetime = Field(default_factory=utc_now, index=True)

    trip: Trip | None = Relationship(back_populates="memory")


class AnalysisJob(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    trip_id: int = Field(foreign_key="trip.id", index=True)
    status: str = Field(default="queued", index=True, max_length=40)
    current_step: str = Field(default="Queued", max_length=300)
    completed_steps: int = Field(default=0, ge=0)
    total_steps: int = Field(default=0, ge=0)
    mode: str = Field(default="all", max_length=40)
    error: str | None = Field(default=None, max_length=2000)
    created_at: datetime = Field(default_factory=utc_now, index=True)
    updated_at: datetime = Field(default_factory=utc_now, index=True)

    trip: Trip | None = Relationship(back_populates="jobs")


class TripQuestion(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    trip_id: int = Field(foreign_key="trip.id", index=True)
    question: str = Field(max_length=1000)
    answer: str = Field(max_length=4000)
    evidence_photo_ids: list[int] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utc_now, index=True)


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item is not None]
