from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
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
    stored_name = f"{uuid4().hex}{upload.extension}"
    stored_path = normalize_stored_path(f"trip_{trip_id}/{stored_name}")
    put_photo_bytes(stored_path, upload.content, upload.mime_type, settings=settings)

    return StoredUpload(
        original_filename=upload.original_filename,
        stored_path=stored_path,
        content=upload.content,
        content_sha256=upload.content_sha256,
        byte_size=upload.byte_size,
        mime_type=upload.mime_type,
    )


def normalize_stored_path(stored_path: str) -> str:
    cleaned = stored_path.replace("\\", "/").lstrip("/")
    parts = Path(cleaned).parts
    if not parts or ".." in parts:
        raise ImageValidationError("Stored image path escapes upload directory")
    return "/".join(parts)


def stored_photo_path(stored_path: str, settings: Settings | None = None) -> Path:
    settings = settings or get_settings()
    upload_root = settings.upload_dir.resolve()
    candidate = (upload_root / normalize_stored_path(stored_path)).resolve()
    try:
        candidate.relative_to(upload_root)
    except ValueError as exc:
        raise ImageValidationError("Stored image path escapes upload directory") from exc
    return candidate


def put_photo_bytes(
    stored_path: str,
    content: bytes,
    mime_type: str | None = None,
    settings: Settings | None = None,
) -> None:
    settings = settings or get_settings()
    key = normalize_stored_path(stored_path)
    if settings.s3_enabled:
        extra = {}
        if mime_type:
            extra["ContentType"] = mime_type
        _s3_client(settings).put_object(
            Bucket=settings.s3_bucket,
            Key=key,
            Body=content,
            **extra,
        )
        return

    destination = stored_photo_path(key, settings)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)


def read_photo_bytes(stored_path: str, settings: Settings | None = None) -> bytes:
    settings = settings or get_settings()
    key = normalize_stored_path(stored_path)
    if settings.s3_enabled:
        try:
            response = _s3_client(settings).get_object(
                Bucket=settings.s3_bucket,
                Key=key,
            )
        except Exception as exc:
            if _is_missing_object(exc):
                raise FileNotFoundError(key) from exc
            raise
        return response["Body"].read()

    path = stored_photo_path(key, settings)
    if not path.exists():
        raise FileNotFoundError(key)
    return path.read_bytes()


def photo_exists(stored_path: str, settings: Settings | None = None) -> bool:
    settings = settings or get_settings()
    try:
        key = normalize_stored_path(stored_path)
    except ImageValidationError:
        return False
    if settings.s3_enabled:
        try:
            _s3_client(settings).head_object(Bucket=settings.s3_bucket, Key=key)
        except Exception as exc:
            if _is_missing_object(exc):
                return False
            raise
        return True
    return stored_photo_path(key, settings).exists()


def delete_stored_photo(stored_path: str, settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    try:
        key = normalize_stored_path(stored_path)
    except ImageValidationError:
        return
    if settings.s3_enabled:
        _s3_client(settings).delete_object(Bucket=settings.s3_bucket, Key=key)
        return
    path = stored_photo_path(key, settings)
    if path.exists():
        path.unlink()


def delete_trip_upload_dir(trip_id: int, settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    prefix = f"trip_{trip_id}/"
    if settings.s3_enabled:
        client = _s3_client(settings)
        paginator = client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=settings.s3_bucket, Prefix=prefix):
            objects = page.get("Contents") or []
            if not objects:
                continue
            client.delete_objects(
                Bucket=settings.s3_bucket,
                Delete={"Objects": [{"Key": item["Key"]} for item in objects]},
            )
        return

    upload_root = settings.upload_dir.resolve()
    trip_dir = (upload_root / f"trip_{trip_id}").resolve()
    try:
        trip_dir.relative_to(upload_root)
    except ValueError as exc:
        raise ImageValidationError("Trip upload path escapes upload directory") from exc
    if trip_dir.exists():
        rmtree(trip_dir)


def _s3_client(settings: Settings):
    return _cached_s3_client(
        settings.s3_endpoint,
        settings.s3_access_key,
        settings.s3_secret_key,
        settings.s3_region,
    )


@lru_cache
def _cached_s3_client(endpoint: str, access_key: str, secret_key: str, region: str):
    import boto3
    from botocore.client import Config

    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region or "us-east-1",
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


def _is_missing_object(exc: Exception) -> bool:
    response = getattr(exc, "response", None)
    if not isinstance(response, dict):
        return False
    error = response.get("Error") or {}
    code = str(error.get("Code") or "")
    return code in {"404", "NoSuchKey", "NotFound", "NoSuchBucket"}
