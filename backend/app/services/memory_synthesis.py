from __future__ import annotations

import re

from sqlmodel import Session, select

from backend.app.db.models import Photo, Trip
from backend.app.schemas.ask import AskResponse


def answer_trip_question(session: Session, trip: Trip, question: str) -> AskResponse:
    photos = session.exec(
        select(Photo).where(Photo.trip_id == trip.id).order_by(Photo.created_at)
    ).all()

    if not photos:
        return AskResponse(
            answer=f"{trip.title} does not have any uploaded photos yet.",
            evidence_photo_ids=[],
        )

    terms = _terms(question)
    matches = [photo for photo in photos if _matches(photo, terms)]
    evidence = matches[:6] if matches else photos[:4]
    evidence_ids = [int(photo.id) for photo in evidence if photo.id is not None]

    if matches:
        answer = (
            f"I found {len(matches)} photo(s) in {trip.title} that match this "
            "question using the saved filenames, metadata, and current analysis records."
        )
    else:
        answer = (
            f"I do not have enough analyzed evidence to answer that precisely for "
            f"{trip.title}. The returned photos are the earliest available memories "
            "for grounding."
        )

    return AskResponse(answer=answer, evidence_photo_ids=evidence_ids)


def _terms(question: str) -> list[str]:
    return [
        term
        for term in re.findall(r"[a-zA-Z0-9]+", question.lower())
        if len(term) >= 3
    ]


def _matches(photo: Photo, terms: list[str]) -> bool:
    if not terms:
        return False

    analysis = photo.analysis
    haystack_parts = [
        photo.filename,
        photo.stored_path,
        str(photo.exif_json),
    ]
    if analysis is not None:
        haystack_parts.extend(
            [
                analysis.scene,
                analysis.mood,
                analysis.memory_prompt,
                " ".join(analysis.activities),
                " ".join(analysis.objects),
            ]
        )
    haystack = " ".join(haystack_parts).lower()
    return any(term in haystack for term in terms)
