from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import pytest
from PIL import Image
from pydantic import BaseModel
from sqlmodel import Session

from backend.app.db.models import Photo, PhotoAnalysis, Trip, TripMemory
from backend.app.workflows.schemas import (
    GroundedTripAnswer,
    PhotoMemoryAnalysis,
    TripMemorySynthesis,
)
from backend.app.workflows.travel_memory import (
    WorkflowInputError,
    analyze_photo_memory,
    answer_trip_question_with_gemma,
    run_trip_memory_workflow,
    synthesize_trip_memory,
)


class FakeGemmaClient:
    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.calls: list[dict[str, Any]] = []

    def complete_json(
        self,
        *,
        messages: Sequence[Mapping[str, Any]],
        schema: type[BaseModel],
        options: Mapping[str, Any],
    ) -> str:
        self.calls.append(
            {
                "messages": messages,
                "schema": schema,
                "options": options,
            }
        )
        if not self.responses:
            raise AssertionError("FakeGemmaClient has no queued response")
        return self.responses.pop(0)


@pytest.fixture
def workflow_session(tmp_path, monkeypatch):
    db_path = tmp_path / "workflow_test.db"
    upload_dir = tmp_path / "uploads"
    monkeypatch.setenv("PMM_DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("PMM_UPLOAD_DIR", str(upload_dir))

    from backend.app.core.config import get_settings
    from backend.app.db.session import get_engine, init_db

    get_settings.cache_clear()
    get_engine.cache_clear()
    init_db()
    with Session(get_engine()) as session:
        yield session, upload_dir

    get_settings.cache_clear()
    get_engine.cache_clear()


def test_analyze_photo_memory_sends_image_and_stores_validated_output(workflow_session):
    session, upload_dir = workflow_session
    trip, photo = _create_trip_with_photo(session, upload_dir)
    client = FakeGemmaClient([_photo_analysis_json()])

    record = analyze_photo_memory(session, int(photo.id), client=client)

    assert record.photo_id == photo.id
    assert record.scene == "A quiet canal street with tiled buildings."
    assert record.memory_prompt == "Canal walk after lunch"
    assert record.activities == ["walking", "sightseeing"]
    assert record.raw_model_json["prompt_version"] == "travel-memory-v1"
    assert client.calls[0]["schema"] is PhotoMemoryAnalysis
    assert client.calls[0]["messages"][0]["role"] == "system"
    assert "[Role]" in client.calls[0]["messages"][0]["content"]
    assert "[Task]" in client.calls[0]["messages"][0]["content"]
    assert "[Expected output]" in client.calls[0]["messages"][0]["content"]
    assert "[Rules]" in client.calls[0]["messages"][0]["content"]
    assert "Do not call tools" in client.calls[0]["messages"][0]["content"]
    assert client.calls[0]["messages"][1]["role"] == "user"
    assert isinstance(client.calls[0]["messages"][1]["images"][0], bytes)


def test_photo_analysis_retries_invalid_json_once(workflow_session):
    session, upload_dir = workflow_session
    _trip, photo = _create_trip_with_photo(session, upload_dir)
    client = FakeGemmaClient(["not json", _photo_analysis_json()])

    record = analyze_photo_memory(session, int(photo.id), client=client)

    assert record.scene
    assert len(client.calls) == 2
    assert "Validation failure" in client.calls[1]["messages"][-1]["content"]


def test_synthesize_trip_memory_stores_trip_level_reasoning(workflow_session):
    session, upload_dir = workflow_session
    trip, photo = _create_trip_with_photo(session, upload_dir)
    _store_photo_analysis(session, int(photo.id))
    client = FakeGemmaClient([_trip_synthesis_json([int(photo.id)])])

    memory = synthesize_trip_memory(session, int(trip.id), client=client)

    assert memory.trip_id == trip.id
    assert memory.narrative_summary == "A slow city walk shaped by canals and architecture."
    assert memory.inferred_interests == ["walkable neighborhoods", "historic architecture"]
    assert memory.evidence_photo_ids == [photo.id]
    assert memory.raw_model_json["trip_memory"]["recurring_themes"] == ["calm streets"]
    assert client.calls[0]["schema"] is TripMemorySynthesis


def test_answer_trip_question_uses_gemma_and_validates_evidence_ids(workflow_session):
    session, upload_dir = workflow_session
    trip, photo = _create_trip_with_photo(session, upload_dir)
    _store_photo_analysis(session, int(photo.id))
    session.add(
        TripMemory(
            trip_id=int(trip.id),
            narrative_summary="A walk through old streets.",
            evidence_photo_ids=[int(photo.id)],
            raw_model_json={},
        )
    )
    session.commit()
    client = FakeGemmaClient(
        [
            _answer_json(
                "The trip seems centered on slow walks and architecture.",
                [int(photo.id)],
            )
        ]
    )

    response = answer_trip_question_with_gemma(
        session,
        int(trip.id),
        "What did I seem drawn to?",
        client=client,
    )

    assert response.answer == "The trip seems centered on slow walks and architecture."
    assert response.evidence_photo_ids == [photo.id]
    assert client.calls[0]["schema"] is GroundedTripAnswer
    assert "[Expected output]" in client.calls[0]["messages"][0]["content"]
    assert "allowed_photo_ids" in client.calls[0]["messages"][1]["content"]


def test_answer_trip_question_retries_invalid_evidence_id(workflow_session):
    session, upload_dir = workflow_session
    trip, photo = _create_trip_with_photo(session, upload_dir)
    _store_photo_analysis(session, int(photo.id))
    client = FakeGemmaClient(
        [
            _answer_json("Invented evidence.", [999]),
            _answer_json("Grounded evidence.", [int(photo.id)]),
        ]
    )

    response = answer_trip_question_with_gemma(
        session,
        int(trip.id),
        "Which moment felt calm?",
        client=client,
    )

    assert response.answer == "Grounded evidence."
    assert response.evidence_photo_ids == [photo.id]
    assert len(client.calls) == 2


def test_missing_photo_image_raises_input_error(workflow_session):
    session, _upload_dir = workflow_session
    trip = Trip(title="No Image")
    session.add(trip)
    session.commit()
    session.refresh(trip)
    photo = Photo(
        trip_id=int(trip.id),
        filename="missing.jpg",
        stored_path="trip_1/missing.jpg",
    )
    session.add(photo)
    session.commit()
    session.refresh(photo)

    with pytest.raises(WorkflowInputError):
        analyze_photo_memory(session, int(photo.id), client=FakeGemmaClient([]))


def test_qa_rejects_context_larger_than_config(workflow_session, monkeypatch):
    session, upload_dir = workflow_session
    monkeypatch.setenv("PMM_WORKFLOW_MAX_QA_PHOTOS", "1")

    from backend.app.core.config import get_settings

    get_settings.cache_clear()
    trip, first_photo = _create_trip_with_photo(session, upload_dir)
    second_photo = _create_photo(session, int(trip.id), upload_dir, "second.jpg")
    _store_photo_analysis(session, int(first_photo.id))
    _store_photo_analysis(session, int(second_photo.id))

    with pytest.raises(WorkflowInputError):
        answer_trip_question_with_gemma(
            session,
            int(trip.id),
            "What happened?",
            client=FakeGemmaClient([]),
        )


def test_run_trip_memory_workflow_runs_fixed_sequence(workflow_session):
    session, upload_dir = workflow_session
    trip, photo = _create_trip_with_photo(session, upload_dir)
    client = FakeGemmaClient(
        [
            _photo_analysis_json(),
            _trip_synthesis_json([int(photo.id)]),
        ]
    )

    result = run_trip_memory_workflow(session, int(trip.id), client=client)

    assert result.analyzed_photo_ids == [photo.id]
    assert result.trip_memory_created is True
    assert result.qa_ready is True
    assert session.get(TripMemory, int(trip.id)) is not None


def _create_trip_with_photo(session: Session, upload_dir: Path) -> tuple[Trip, Photo]:
    trip = Trip(title="Porto Weekend", description="Tiles and river walks.")
    session.add(trip)
    session.commit()
    session.refresh(trip)
    photo = _create_photo(session, int(trip.id), upload_dir, "canal.jpg")
    return trip, photo


def _create_photo(
    session: Session,
    trip_id: int,
    upload_dir: Path,
    filename: str,
) -> Photo:
    relative = Path(f"trip_{trip_id}") / filename
    absolute = upload_dir / relative
    absolute.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (16, 12), color="teal").save(absolute, format="JPEG")
    photo = Photo(
        trip_id=trip_id,
        filename=filename,
        stored_path=relative.as_posix(),
        latitude=41.1579,
        longitude=-8.6291,
        exif_json={"Camera": "Test"},
    )
    session.add(photo)
    session.commit()
    session.refresh(photo)
    return photo


def _store_photo_analysis(session: Session, photo_id: int) -> None:
    payload = PhotoMemoryAnalysis.model_validate_json(_photo_analysis_json())
    session.add(
        PhotoAnalysis(
            photo_id=photo_id,
            scene=payload.scene_summary,
            activities=payload.visible_activities,
            objects=payload.visible_objects,
            mood=payload.mood,
            memory_prompt=payload.memory_caption,
            confidence=payload.confidence,
            raw_model_json={
                "prompt_version": "travel-memory-v1",
                "photo_memory": payload.model_dump(),
            },
        )
    )
    session.commit()


def _photo_analysis_json() -> str:
    return json.dumps(
        {
            "scene_summary": "A quiet canal street with tiled buildings.",
            "memory_caption": "Canal walk after lunch",
            "place_type": "historic street",
            "visible_activities": ["walking", "sightseeing"],
            "visible_objects": ["canal", "tiles", "balconies"],
            "sensory_details": ["soft daylight", "calm water"],
            "inferred_interest_signals": ["architecture", "slow walks"],
            "mood": "calm",
            "uncertainty_notes": ["Exact neighborhood cannot be confirmed from image alone."],
            "confidence": 0.82,
        }
    )


def _trip_synthesis_json(photo_ids: list[int]) -> str:
    return json.dumps(
        {
            "narrative_summary": "A slow city walk shaped by canals and architecture.",
            "inferred_interests": ["walkable neighborhoods", "historic architecture"],
            "recurring_themes": ["calm streets"],
            "memorable_moments": [
                {
                    "title": "Canal walk",
                    "description": "A quiet walk near tiled buildings.",
                    "evidence_photo_ids": photo_ids,
                }
            ],
            "evidence_photo_ids": photo_ids,
            "uncertainty_notes": ["The exact route is not known."],
        }
    )


def _answer_json(answer: str, evidence_photo_ids: list[int]) -> str:
    return json.dumps(
        {
            "answer": answer,
            "evidence_photo_ids": evidence_photo_ids,
            "uncertainty": "",
        }
    )
