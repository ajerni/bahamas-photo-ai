from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from shutil import rmtree
from uuid import uuid4

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

from backend.app.core.config import Settings, get_settings


class ImageValidationError(ValueError):
    pass


class ImageTooLargeError(ValueError):
    pass


@dataclass(frozen=True)
class StoredUpload:
    original_filename: str
    stored_path: str
    content: bytes
    content_sha256: str
    byte_size: int
    mime_type: str


@dataclass(frozen=True)
class ValidatedUpload:
    original_filename: str
    content: bytes
    content_sha256: str
    byte_size: int
    mime_type: str
    extension: str


CONTENT_TYPE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


async def save_image_upload(
    upload: UploadFile,
    trip_id: int,
    settings: Settings | None = None,
) -> StoredUpload:
    settings = settings or get_settings()
    validated = await validate_image_upload(upload, settings)
    return store_validated_upload(validated, trip_id=trip_id, settings=settings)


async def validate_image_upload(
    upload: UploadFile,
    settings: Settings | None = None,
) -> ValidatedUpload:
    settings = settings or get_settings()
    content_type = upload.content_type or ""
    if content_type not in settings.allowed_image_types:
        raise ImageValidationError(f"Unsupported image type: {content_type or 'unknown'}")

    content = await upload.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise ImageTooLargeError(f"Image exceeds {settings.max_upload_mb} MB")

    try:
        with Image.open(BytesIO(content)) as image:
            image.verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise ImageValidationError("Uploaded file is not a valid image") from exc

    original_name = Path(upload.filename or "photo").name
    extension = CONTENT_TYPE_EXTENSIONS.get(content_type, Path(original_name).suffix)
    return ValidatedUpload(
        original_filename=original_name,
        content=content,
        content_sha256=sha256(content).hexdigest(),
        byte_size=len(content),
        mime_type=content_type,
        extension=extension,
    )


def store_validated_upload(
    upload: ValidatedUpload,
    trip_id: int,
    settings: Settings | None = None,
) -> StoredUpload:
    settings = settings or get_settings()
    trip_dir = settings.upload_dir / f"trip_{trip_id}"
    trip_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid4().hex}{upload.extension}"
    destination = trip_dir / stored_name
    destination.write_bytes(upload.content)

    return StoredUpload(
        original_filename=upload.original_filename,
        stored_path=f"trip_{trip_id}/{stored_name}",
        content=upload.content,
        content_sha256=upload.content_sha256,
        byte_size=upload.byte_size,
        mime_type=upload.mime_type,
    )


def stored_photo_path(stored_path: str, settings: Settings | None = None) -> Path:
    settings = settings or get_settings()
    upload_root = settings.upload_dir.resolve()
    candidate = (upload_root / stored_path).resolve()
    try:
        candidate.relative_to(upload_root)
    except ValueError as exc:
        raise ImageValidationError("Stored image path escapes upload directory") from exc
    return candidate


def delete_stored_photo(stored_path: str, settings: Settings | None = None) -> None:
    path = stored_photo_path(stored_path, settings)
    if path.exists():
        path.unlink()


def delete_trip_upload_dir(trip_id: int, settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    upload_root = settings.upload_dir.resolve()
    trip_dir = (upload_root / f"trip_{trip_id}").resolve()
    try:
        trip_dir.relative_to(upload_root)
    except ValueError as exc:
        raise ImageValidationError("Trip upload path escapes upload directory") from exc
    if trip_dir.exists():
        rmtree(trip_dir)
