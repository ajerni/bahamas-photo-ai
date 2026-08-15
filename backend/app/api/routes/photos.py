from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlmodel import Session, select

from backend.app.api.deps import get_photo_or_404, get_trip_or_404
from backend.app.api.serializers import photo_to_read
from backend.app.core.config import get_settings
from backend.app.db.models import Photo, PhotoAnalysis, Trip, utc_now
from backend.app.db.session import get_session
from backend.app.schemas.photo import (
    PhotoImportResponse,
    PhotoImportResult,
    PhotoRead,
    PhotoUpdate,
)
from backend.app.services.exif import extract_exif
from backend.app.services.storage import (
    delete_stored_photo,
    ImageTooLargeError,
    ImageValidationError,
    save_image_upload,
    store_validated_upload,
    validate_image_upload,
)

router = APIRouter(tags=["photos"])


@router.post("/trips/{trip_id}/photos", response_model=list[PhotoRead])
async def upload_trip_photos(
    files: list[UploadFile] = File(...),
    trip: Trip = Depends(get_trip_or_404),
    session: Session = Depends(get_session),
) -> list[PhotoRead]:
    created: list[Photo] = []
    settings = get_settings()
    trip_id = int(trip.id)
    for upload in files:
        try:
            stored = await save_image_upload(upload, trip_id=trip_id, settings=settings)
        except ImageTooLargeError as exc:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc)) from exc
        except ImageValidationError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        exif = extract_exif(stored.content)
        photo = Photo(
            trip_id=trip_id,
            filename=stored.original_filename,
            stored_path=stored.stored_path,
            content_sha256=stored.content_sha256,
            byte_size=stored.byte_size,
            mime_type=stored.mime_type,
            captured_at=exif.captured_at,
            latitude=exif.latitude,
            longitude=exif.longitude,
            exif_json=exif.raw,
        )
        session.add(photo)
        created.append(photo)

    session.commit()
    for photo in created:
        session.refresh(photo)
    return [photo_to_read(photo) for photo in created]


@router.post("/trips/{trip_id}/photos/import", response_model=PhotoImportResponse)
async def import_trip_photos(
    files: list[UploadFile] = File(...),
    trip: Trip = Depends(get_trip_or_404),
    session: Session = Depends(get_session),
) -> PhotoImportResponse:
    results: list[PhotoImportResult] = []
    settings = get_settings()
    trip_id = int(trip.id)

    for upload in files:
        filename = upload.filename or "photo"
        try:
            validated = await validate_image_upload(upload, settings)
        except (ImageTooLargeError, ImageValidationError) as exc:
            results.append(
                PhotoImportResult(
                    filename=filename,
                    status="rejected",
                    detail=str(exc),
                )
            )
            continue

        duplicate = session.exec(
            select(Photo).where(
                Photo.trip_id == trip_id,
                Photo.content_sha256 == validated.content_sha256,
            )
        ).first()
        if duplicate is not None:
            results.append(
                PhotoImportResult(
                    filename=validated.original_filename,
                    status="duplicate",
                    detail="Already imported for this trip",
                    photo=photo_to_read(duplicate),
                )
            )
            continue

        stored = store_validated_upload(validated, trip_id=trip_id, settings=settings)
        exif = extract_exif(stored.content)
        photo = Photo(
            trip_id=trip_id,
            filename=stored.original_filename,
            stored_path=stored.stored_path,
            content_sha256=stored.content_sha256,
            byte_size=stored.byte_size,
            mime_type=stored.mime_type,
            captured_at=exif.captured_at,
            latitude=exif.latitude,
            longitude=exif.longitude,
            exif_json=exif.raw,
        )
        try:
            session.add(photo)
            session.commit()
            session.refresh(photo)
        except Exception:
            session.rollback()
            delete_stored_photo(stored.stored_path, settings)
            raise
        results.append(
            PhotoImportResult(
                filename=stored.original_filename,
                status="stored",
                photo=photo_to_read(photo),
            )
        )

    return PhotoImportResponse(
        results=results,
        stored_count=sum(1 for item in results if item.status == "stored"),
        duplicate_count=sum(1 for item in results if item.status == "duplicate"),
        rejected_count=sum(1 for item in results if item.status == "rejected"),
    )


@router.get("/trips/{trip_id}/photos", response_model=list[PhotoRead])
def list_trip_photos(
    trip: Trip = Depends(get_trip_or_404),
    session: Session = Depends(get_session),
) -> list[PhotoRead]:
    trip_id = int(trip.id)
    photos = session.exec(
        select(Photo).where(Photo.trip_id == trip_id).order_by(Photo.created_at)
    ).all()
    return [photo_to_read(photo) for photo in photos]


@router.patch("/photos/{photo_id}", response_model=PhotoRead)
def update_photo(
    payload: PhotoUpdate,
    photo: Photo = Depends(get_photo_or_404),
    session: Session = Depends(get_session),
) -> PhotoRead:
    if payload.is_favorite is not None:
        photo.is_favorite = payload.is_favorite

    memory_fields = {
        "user_memory_caption",
        "user_scene_summary",
        "user_mood",
        "user_note",
    }
    if memory_fields.intersection(payload.model_fields_set):
        analysis = session.get(PhotoAnalysis, int(photo.id))
        if analysis is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Analyze this photo before editing memory",
            )
        for field_name in memory_fields.intersection(payload.model_fields_set):
            setattr(analysis, field_name, _clean_optional(getattr(payload, field_name)))
        analysis.updated_at = utc_now()
        session.add(analysis)

    session.add(photo)
    session.commit()
    session.refresh(photo)
    return photo_to_read(photo)


@router.delete("/photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_photo(
    photo: Photo = Depends(get_photo_or_404),
    session: Session = Depends(get_session),
) -> Response:
    photo_id = int(photo.id)
    trip = session.get(Trip, photo.trip_id)
    if trip is not None and trip.cover_photo_id == photo_id:
        trip.cover_photo_id = None
        session.add(trip)

    analysis = session.get(PhotoAnalysis, photo_id)
    if analysis is not None:
        session.delete(analysis)
    stored_path = photo.stored_path
    session.delete(photo)
    session.commit()
    delete_stored_photo(stored_path)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip() or None
