from __future__ import annotations

import json
from io import BytesIO
from typing import Any, Mapping, Sequence

from PIL import Image
from pydantic import BaseModel

from backend.app.schemas.ask import AskResponse


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
        self.calls.append({"messages": messages, "schema": schema, "options": options})
        if not self.responses:
            raise AssertionError("No fake Gemma response queued")
        return self.responses.pop(0)


def test_analyze_route_creates_job_and_stores_workflow_outputs(client, monkeypatch):
    from backend.app.api.routes import analysis

    fake_client = FakeGemmaClient(
        [
            _photo_analysis_json(),
            _trip_synthesis_json([1]),
        ]
    )
    monkeypatch.setattr(analysis, "get_gemma_client", lambda: fake_client)

    trip = client.post("/api/trips", json={"title": "Porto"}).json()
    upload_response = client.post(
        f"/api/trips/{trip['id']}/photos",
        files=[("files", ("porto.jpg", _image_bytes(), "image/jpeg"))],
    )
    assert upload_response.status_code == 200

    response = client.post(f"/api/trips/{trip['id']}/analyze")

    assert response.status_code == 202
    created_job = response.json()
    assert created_job["status"] == "queued"
    assert created_job["total_steps"] == 2

    job_response = client.get(f"/api/jobs/{created_job['id']}")
    assert job_response.status_code == 200
    job = job_response.json()
    assert job["status"] == "completed"
    assert job["completed_steps"] == 2

    detail = client.get(f"/api/trips/{trip['id']}").json()
    assert detail["memory"]["narrative_summary"] == "A bright walk through tiled streets."
    assert detail["photos"][0]["analysis"]["memory_caption"] == "Blue tiles in afternoon light"
    assert detail["photos"][0]["analysis"]["place_type"] == "historic street"


def test_analysis_and_job_routes_return_404_for_missing_records(client):
    analyze_response = client.post("/api/trips/999/analyze")
    assert analyze_response.status_code == 404
    assert analyze_response.json()["detail"] == "Trip not found"

    job_response = client.get("/api/jobs/999")
    assert job_response.status_code == 404
    assert job_response.json()["detail"] == "Job not found"


def test_analyze_route_marks_job_failed_when_workflow_fails(client, monkeypatch):
    from backend.app.api.routes import analysis

    fake_client = FakeGemmaClient(["not json", "still not json"])
    monkeypatch.setattr(analysis, "get_gemma_client", lambda: fake_client)

    trip = client.post("/api/trips", json={"title": "Broken"}).json()
    client.post(
        f"/api/trips/{trip['id']}/photos",
        files=[("files", ("broken.jpg", _image_bytes(), "image/jpeg"))],
    )

    response = client.post(f"/api/trips/{trip['id']}/analyze")

    assert response.status_code == 202
    job = client.get(f"/api/jobs/{response.json()['id']}").json()
    assert job["status"] == "failed"
    assert job["error"]


def test_ask_route_uses_workflow_function(client, monkeypatch):
    from backend.app.api.routes import ask

    called: dict[str, Any] = {}

    def fake_answer(session, trip_id: int, question: str):
        called["trip_id"] = trip_id
        called["question"] = question
        return AskResponse(answer="Grounded answer", evidence_photo_ids=[7])

    monkeypatch.setattr(ask, "answer_trip_question_with_gemma", fake_answer)
    trip = client.post("/api/trips", json={"title": "Q&A"}).json()

    response = client.post(
        f"/api/trips/{trip['id']}/ask",
        json={"question": "What did I like?"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "Grounded answer",
        "evidence_photo_ids": [7],
    }
    assert called == {"trip_id": trip["id"], "question": "What did I like?"}


def test_ask_route_returns_404_for_missing_trip(client):
    response = client.post(
        "/api/trips/999/ask",
        json={"question": "What did I like?"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Trip not found"


def _image_bytes() -> bytes:
    image = BytesIO()
    Image.new("RGB", (12, 10), color="navy").save(image, format="JPEG")
    return image.getvalue()


def _photo_analysis_json() -> str:
    return json.dumps(
        {
            "scene_summary": "A tiled street with soft afternoon light.",
            "memory_caption": "Blue tiles in afternoon light",
            "place_type": "historic street",
            "visible_activities": ["walking"],
            "visible_objects": ["tiles", "street"],
            "sensory_details": ["warm light"],
            "inferred_interest_signals": ["architecture"],
            "mood": "curious",
            "uncertainty_notes": [],
            "confidence": 0.86,
        }
    )


def _trip_synthesis_json(photo_ids: list[int]) -> str:
    return json.dumps(
        {
            "narrative_summary": "A bright walk through tiled streets.",
            "inferred_interests": ["architecture"],
            "recurring_themes": ["tiles"],
            "memorable_moments": [
                {
                    "title": "Tile walk",
                    "description": "A quiet street scene with tiles.",
                    "evidence_photo_ids": photo_ids,
                }
            ],
            "evidence_photo_ids": photo_ids,
            "uncertainty_notes": [],
        }
    )
