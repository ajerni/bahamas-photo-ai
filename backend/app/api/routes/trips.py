from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlmodel import Session, select

from backend.app.api.deps import get_trip_or_404
from backend.app.api.serializers import photo_to_read
from backend.app.db.models import AnalysisJob, Photo, PhotoAnalysis, Trip, TripMemory, TripQuestion
from backend.app.db.session import get_session
from backend.app.schemas.analysis import TripMemoryRead, TripMemoryUpdate
from backend.app.schemas.job import AnalysisJobRead
from backend.app.schemas.question import TripQuestionRead
from backend.app.schemas.trip import TripCreate, TripDetail, TripRead, TripUpdate
from backend.app.services.markdown_export import (
    export_filename,
    export_zip_filename,
    trip_markdown,
    trip_zip_bytes,
)
from backend.app.services.storage import delete_trip_upload_dir

router = APIRouter(prefix="/trips", tags=["trips"])
RECOVERABLE_JOB_STATUSES = {"queued", "running", "cancel_requested", "failed", "canceled"}


@router.post("", response_model=TripRead, status_code=status.HTTP_201_CREATED)
def create_trip(payload: TripCreate, session: Session = Depends(get_session)) -> TripRead:
    trip = Trip(title=payload.title.strip(), description=payload.description)
    session.add(trip)
    session.commit()
    session.refresh(trip)
    return TripRead.model_validate(trip)


@router.get("", response_model=list[TripRead])
def list_trips(session: Session = Depends(get_session)) -> list[TripRead]:
    trips = session.exec(select(Trip).order_by(Trip.created_at.desc())).all()
    return [TripRead.model_validate(trip) for trip in trips]


@router.patch("/{trip_id}", response_model=TripRead)
def update_trip(
    payload: TripUpdate,
    trip: Trip = Depends(get_trip_or_404),
    session: Session = Depends(get_session),
) -> TripRead:
    if payload.title is not None:
        trip.title = payload.title.strip()
    if "description" in payload.model_fields_set:
        trip.description = payload.description.strip() if payload.description else None
    if "cover_photo_id" in payload.model_fields_set:
        _validate_trip_photo(session, int(trip.id), payload.cover_photo_id)
        trip.cover_photo_id = payload.cover_photo_id

    session.add(trip)
    session.commit()
    session.refresh(trip)
    return TripRead.model_validate(trip)


@router.get("/{trip_id}", response_model=TripDetail)
def get_trip(
    trip: Trip = Depends(get_trip_or_404),
    session: Session = Depends(get_session),
) -> TripDetail:
    trip_id = int(trip.id)
    photos = session.exec(
        select(Photo).where(Photo.trip_id == trip_id).order_by(Photo.created_at)
    ).all()
    memory = session.get(TripMemory, trip_id)
    questions = session.exec(
        select(TripQuestion)
        .where(TripQuestion.trip_id == trip_id)
        .order_by(TripQuestion.created_at)
    ).all()
    return TripDetail(
        id=int(trip.id),
        title=trip.title,
        description=trip.description,
        cover_photo_id=trip.cover_photo_id,
        created_at=trip.created_at,
        photos=[photo_to_read(photo) for photo in photos],
        memory=TripMemoryRead.model_validate(memory) if memory is not None else None,
        questions=[TripQuestionRead.model_validate(question) for question in questions],
    )


@router.get("/{trip_id}/jobs/latest", response_model=AnalysisJobRead | None)
def get_latest_trip_job(
    trip: Trip = Depends(get_trip_or_404),
    session: Session = Depends(get_session),
) -> AnalysisJobRead | None:
    job = session.exec(
        select(AnalysisJob)
        .where(
            AnalysisJob.trip_id == int(trip.id),
            AnalysisJob.status.in_(RECOVERABLE_JOB_STATUSES),
        )
        .order_by(AnalysisJob.updated_at.desc())
    ).first()
    return AnalysisJobRead.model_validate(job) if job is not None else None


@router.patch("/{trip_id}/memory", response_model=TripMemoryRead)
def update_trip_memory(
    payload: TripMemoryUpdate,
    trip: Trip = Depends(get_trip_or_404),
    session: Session = Depends(get_session),
) -> TripMemoryRead:
    memory = session.get(TripMemory, int(trip.id))
    if memory is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Analyze this trip before editing trip memory",
        )

    if "user_narrative_summary" in payload.model_fields_set:
        memory.user_narrative_summary = _clean_optional(payload.user_narrative_summary)
    if "user_note" in payload.model_fields_set:
        memory.user_note = _clean_optional(payload.user_note)

    session.add(memory)
    session.commit()
    session.refresh(memory)
    return TripMemoryRead.model_validate(memory)


@router.delete("/{trip_id}/analysis", status_code=status.HTTP_204_NO_CONTENT)
def clear_trip_analysis(
    trip: Trip = Depends(get_trip_or_404),
    session: Session = Depends(get_session),
) -> Response:
    trip_id = int(trip.id)
    photos = session.exec(select(Photo).where(Photo.trip_id == trip_id)).all()
    for photo in photos:
        analysis = session.get(PhotoAnalysis, int(photo.id))
        if analysis is not None:
            session.delete(analysis)
    memory = session.get(TripMemory, trip_id)
    if memory is not None:
        session.delete(memory)
    for question in session.exec(
        select(TripQuestion).where(TripQuestion.trip_id == trip_id)
    ).all():
        session.delete(question)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{trip_id}/export.md")
def export_trip_markdown(
    trip: Trip = Depends(get_trip_or_404),
    session: Session = Depends(get_session),
) -> Response:
    trip_id = int(trip.id)
    photos = session.exec(
        select(Photo).where(Photo.trip_id == trip_id).order_by(Photo.created_at)
    ).all()
    memory = session.get(TripMemory, trip_id)
    questions = session.exec(
        select(TripQuestion)
        .where(TripQuestion.trip_id == trip_id)
        .order_by(TripQuestion.created_at)
    ).all()
    filename = export_filename(trip.title)
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(
        content=trip_markdown(trip, photos, memory, questions),
        media_type="text/markdown",
        headers=headers,
    )


@router.get("/{trip_id}/export.zip")
def export_trip_zip(
    trip: Trip = Depends(get_trip_or_404),
    session: Session = Depends(get_session),
) -> Response:
    trip_id = int(trip.id)
    photos = session.exec(
        select(Photo).where(Photo.trip_id == trip_id).order_by(Photo.created_at)
    ).all()
    memory = session.get(TripMemory, trip_id)
    questions = session.exec(
        select(TripQuestion)
        .where(TripQuestion.trip_id == trip_id)
        .order_by(TripQuestion.created_at)
    ).all()
    filename = export_zip_filename(trip.title)
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(
        content=trip_zip_bytes(trip, photos, memory, questions),
        media_type="application/zip",
        headers=headers,
    )


@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trip(
    trip: Trip = Depends(get_trip_or_404),
    session: Session = Depends(get_session),
) -> Response:
    trip_id = int(trip.id)
    photos = session.exec(select(Photo).where(Photo.trip_id == trip_id)).all()
    for photo in photos:
        analysis = session.get(PhotoAnalysis, int(photo.id))
        if analysis is not None:
            session.delete(analysis)
        session.delete(photo)

    memory = session.get(TripMemory, trip_id)
    if memory is not None:
        session.delete(memory)
    for job in session.exec(select(AnalysisJob).where(AnalysisJob.trip_id == trip_id)).all():
        session.delete(job)
    for question in session.exec(
        select(TripQuestion).where(TripQuestion.trip_id == trip_id)
    ).all():
        session.delete(question)
    session.delete(trip)
    session.commit()
    delete_trip_upload_dir(trip_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _validate_trip_photo(
    session: Session,
    trip_id: int,
    photo_id: int | None,
) -> None:
    if photo_id is None:
        return
    photo = session.get(Photo, photo_id)
    if photo is None or photo.trip_id != trip_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cover photo must belong to this trip",
        )


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip() or None
