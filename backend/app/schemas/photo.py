from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.analysis import PhotoAnalysisRead


class PhotoRead(BaseModel):
    id: int
    trip_id: int
    filename: str
    stored_path: str
    image_url: str
    content_sha256: str | None = None
    byte_size: int | None = None
    mime_type: str | None = None
    captured_at: datetime | None
    latitude: float | None
    longitude: float | None
    exif_json: dict[str, Any]
    is_favorite: bool
    created_at: datetime
    analysis: PhotoAnalysisRead | None = None

    model_config = ConfigDict(from_attributes=True)


class PhotoUpdate(BaseModel):
    is_favorite: bool | None = None
    user_memory_caption: str | None = Field(default=None, max_length=1000)
    user_scene_summary: str | None = Field(default=None, max_length=500)
    user_mood: str | None = Field(default=None, max_length=160)
    user_note: str | None = Field(default=None, max_length=2000)


class PhotoImportResult(BaseModel):
    filename: str
    status: str
    detail: str | None = None
    photo: PhotoRead | None = None


class PhotoImportResponse(BaseModel):
    results: list[PhotoImportResult]
    stored_count: int
    duplicate_count: int
    rejected_count: int
