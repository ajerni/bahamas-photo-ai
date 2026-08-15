from __future__ import annotations

from fastapi import Depends, HTTPException, status
from sqlmodel import Session

from backend.app.db.models import AnalysisJob, Photo, Trip
from backend.app.db.session import get_session


def get_trip_or_404(
    trip_id: int,
    session: Session = Depends(get_session),
) -> Trip:
    trip = session.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    return trip


def get_job_or_404(
    job_id: int,
    session: Session = Depends(get_session),
) -> AnalysisJob:
    job = session.get(AnalysisJob, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


def get_photo_or_404(
    photo_id: int,
    session: Session = Depends(get_session),
) -> Photo:
    photo = session.get(Photo, photo_id)
    if photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    return photo
