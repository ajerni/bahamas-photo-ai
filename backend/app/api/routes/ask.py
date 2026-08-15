from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from backend.app.api.deps import get_trip_or_404
from backend.app.api.errors import workflow_bad_request
from backend.app.db.models import Trip, TripQuestion
from backend.app.db.session import get_session
from backend.app.schemas.ask import AskRequest, AskResponse
from backend.app.schemas.question import TripQuestionRead
from backend.app.workflows.travel_memory import (
    WorkflowError,
    answer_trip_question_with_gemma,
)

router = APIRouter(prefix="/trips", tags=["ask"])


@router.post("/{trip_id}/ask", response_model=AskResponse)
def ask_trip(
    payload: AskRequest,
    trip: Trip = Depends(get_trip_or_404),
    session: Session = Depends(get_session),
) -> AskResponse:
    try:
        response = answer_trip_question_with_gemma(session, int(trip.id), payload.question)
    except WorkflowError as exc:
        raise workflow_bad_request(exc) from exc

    record = TripQuestion(
        trip_id=int(trip.id),
        question=payload.question,
        answer=response.answer,
        evidence_photo_ids=response.evidence_photo_ids,
    )
    session.add(record)
    session.commit()
    return response


@router.get("/{trip_id}/questions", response_model=list[TripQuestionRead])
def list_trip_questions(
    trip: Trip = Depends(get_trip_or_404),
    session: Session = Depends(get_session),
) -> list[TripQuestionRead]:
    questions = session.exec(
        select(TripQuestion)
        .where(TripQuestion.trip_id == int(trip.id))
        .order_by(TripQuestion.created_at)
    ).all()
    return [TripQuestionRead.model_validate(question) for question in questions]
