from __future__ import annotations

import json
from io import BytesIO
from typing import Any, Mapping, Sequence
from zipfile import ZipFile

from PIL import Image
from pydantic import BaseModel
from sqlmodel import Session


class FakeGemmaClient:
    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.calls: list[type[BaseModel]] = []

    def complete_json(
        self,
        *,
        messages: Sequence[Mapping[str, Any]],
        schema: type[BaseModel],
        options: Mapping[str, Any],
    ) -> str:
        self.calls.append(schema)
        if not self.responses:
            raise AssertionError("No fake Gemma response queued")
        return self.responses.pop(0)


def test_import_reports_stored_duplicate_and_rejected_files(client):
    trip = client.post("/api/trips", json={"title": "Import"}).json()
    image = _image_bytes("red")

    response = client.post(
        f"/api/trips/{trip['id']}/photos/import",
        files=[
            ("files", ("first.jpg", image, "image/jpeg")),
            ("files", ("duplicate.jpg", image, "image/jpeg")),
            ("files", ("notes.txt", b"not an image", "text/plain")),
        ],
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["stored_count"] == 1
    assert payload["duplicate_count"] == 1
    assert payload["rejected_count"] == 1
    assert [item["status"] for item in payload["results"]] == [
        "stored",
        "duplicate",
        "rejected",
    ]

    detail = client.get(f"/api/trips/{trip['id']}").json()
    assert len(detail["photos"]) == 1
    assert detail["photos"][0]["content_sha256"]
    assert detail["photos"][0]["byte_size"] == len(image)
    assert detail["photos"][0]["mime_type"] == "image/jpeg"


def test_photo_delete_clears_cover_and_removes_file(client):
    trip = client.post("/api/trips", json={"title": "Delete Photo"}).json()
    photo = _upload_photo(client, trip["id"])
    client.patch(f"/api/trips/{trip['id']}", json={"cover_photo_id": photo["id"]})

    from backend.app.core.config import get_settings

    path = get_settings().upload_dir / photo["stored_path"]
    assert path.exists()

    response = client.delete(f"/api/photos/{photo['id']}")

    assert response.status_code == 204
    assert not path.exists()
    detail = client.get(f"/api/trips/{trip['id']}").json()
    assert detail["cover_photo_id"] is None
    assert detail["photos"] == []


def test_trip_delete_removes_records_and_upload_directory(client):
    trip = client.post("/api/trips", json={"title": "Delete Trip"}).json()
    _upload_photo(client, trip["id"])

    from backend.app.core.config import get_settings

    trip_dir = get_settings().upload_dir / f"trip_{trip['id']}"
    assert trip_dir.exists()

    response = client.delete(f"/api/trips/{trip['id']}")

    assert response.status_code == 204
    assert client.get(f"/api/trips/{trip['id']}").status_code == 404
    assert not trip_dir.exists()


def test_clear_analysis_keeps_photos_and_user_curation(client, monkeypatch):
    trip, photo = _analyzed_trip(client, monkeypatch)
    client.patch(f"/api/photos/{photo['id']}", json={"is_favorite": True})

    from backend.app.db.models import TripQuestion
    from backend.app.db.session import get_engine

    with Session(get_engine()) as session:
        session.add(
            TripQuestion(
                trip_id=trip["id"],
                question="What did I like?",
                answer="Tiles.",
                evidence_photo_ids=[photo["id"]],
            )
        )
        session.commit()

    response = client.delete(f"/api/trips/{trip['id']}/analysis")

    assert response.status_code == 204
    detail = client.get(f"/api/trips/{trip['id']}").json()
    assert detail["memory"] is None
    assert detail["questions"] == []
    assert detail["photos"][0]["analysis"] is None
    assert detail["photos"][0]["is_favorite"] is True


def test_analyze_missing_mode_only_analyzes_new_photos(client, monkeypatch):
    from backend.app.api.routes import analysis
    from backend.app.workflows.schemas import PhotoMemoryAnalysis, TripMemorySynthesis

    fake_all = FakeGemmaClient(
        [_photo_analysis_json("First"), _photo_analysis_json("Second"), _trip_synthesis_json([1, 2])]
    )
    monkeypatch.setattr(analysis, "get_gemma_client", lambda: fake_all)
    trip = client.post("/api/trips", json={"title": "Missing Mode"}).json()
    _upload_photo(client, trip["id"], "one.jpg", "red")
    _upload_photo(client, trip["id"], "two.jpg", "blue")
    response = client.post(f"/api/trips/{trip['id']}/analyze")
    assert response.status_code == 202
    assert client.get(f"/api/jobs/{response.json()['id']}").json()["status"] == "completed"
    assert fake_all.calls.count(PhotoMemoryAnalysis) == 2

    third = _upload_photo(client, trip["id"], "three.jpg", "green")
    fake_missing = FakeGemmaClient(
        [_photo_analysis_json("Third"), _trip_synthesis_json([1, 2, third["id"]])]
    )
    monkeypatch.setattr(analysis, "get_gemma_client", lambda: fake_missing)

    missing_response = client.post(
        f"/api/trips/{trip['id']}/analyze",
        json={"mode": "missing"},
    )

    assert missing_response.status_code == 202
    job = client.get(f"/api/jobs/{missing_response.json()['id']}").json()
    assert job["mode"] == "missing"
    assert job["status"] == "completed"
    assert fake_missing.calls.count(PhotoMemoryAnalysis) == 1
    assert fake_missing.calls.count(TripMemorySynthesis) == 1


def test_job_cancel_and_retry_endpoints(client, monkeypatch):
    from backend.app.api.routes import analysis
    from backend.app.db.models import AnalysisJob, Trip
    from backend.app.db.session import get_engine

    with Session(get_engine()) as session:
        trip = Trip(title="Jobs")
        session.add(trip)
        session.commit()
        session.refresh(trip)
        job = AnalysisJob(
            trip_id=int(trip.id),
            status="queued",
            current_step="Queued",
            completed_steps=0,
            total_steps=0,
            mode="missing",
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        job_id = int(job.id)

    cancel_response = client.post(f"/api/jobs/{job_id}/cancel")
    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "canceled"

    fake = FakeGemmaClient([])
    monkeypatch.setattr(analysis, "get_gemma_client", lambda: fake)
    retry_response = client.post(f"/api/jobs/{job_id}/retry")
    assert retry_response.status_code == 200
    retry = retry_response.json()
    assert retry["id"] != job_id
    assert retry["mode"] == "missing"


def test_latest_trip_job_returns_latest_recoverable_job(client):
    from backend.app.db.models import AnalysisJob, Trip
    from backend.app.db.session import get_engine

    with Session(get_engine()) as session:
        trip = Trip(title="Recover Jobs")
        session.add(trip)
        session.commit()
        session.refresh(trip)
        completed = AnalysisJob(
            trip_id=int(trip.id),
            status="completed",
            current_step="Completed",
            completed_steps=2,
            total_steps=2,
            mode="all",
        )
        failed = AnalysisJob(
            trip_id=int(trip.id),
            status="failed",
            current_step="Failed",
            completed_steps=1,
            total_steps=2,
            mode="missing",
            error="Model stopped",
        )
        session.add(completed)
        session.add(failed)
        session.commit()
        session.refresh(trip)

    response = client.get(f"/api/trips/{trip.id}/jobs/latest")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "failed"
    assert payload["mode"] == "missing"
    assert payload["error"] == "Model stopped"


def test_ask_stores_question_history_and_trip_detail_includes_it(client, monkeypatch):
    from backend.app.api.routes import ask
    from backend.app.schemas.ask import AskResponse

    def fake_answer(session, trip_id: int, question: str):
        return AskResponse(answer="You liked quiet streets.", evidence_photo_ids=[3])

    monkeypatch.setattr(ask, "answer_trip_question_with_gemma", fake_answer)
    trip = client.post("/api/trips", json={"title": "Questions"}).json()

    response = client.post(
        f"/api/trips/{trip['id']}/ask",
        json={"question": "What did I like?"},
    )

    assert response.status_code == 200
    questions = client.get(f"/api/trips/{trip['id']}/questions").json()
    assert questions[0]["question"] == "What did I like?"
    assert questions[0]["answer"] == "You liked quiet streets."
    assert client.get(f"/api/trips/{trip['id']}").json()["questions"] == questions


def test_zip_export_contains_dossier_files_and_content(client, monkeypatch):
    trip, photo = _analyzed_trip(client, monkeypatch)
    client.patch(
        f"/api/photos/{photo['id']}",
        json={"is_favorite": True, "user_note": "A private photo note."},
    )

    response = client.get(f"/api/trips/{trip['id']}/export.zip")

    assert response.status_code == 200
    with ZipFile(BytesIO(response.content)) as archive:
        names = set(archive.namelist())
        assert {"index.html", "memory.md", "metadata.json"} <= names
        assert any(name.startswith("photos/") for name in names)
        html = archive.read("index.html").decode()
        metadata = json.loads(archive.read("metadata.json").decode())

    assert "A bright walk through tiled streets." in html
    assert metadata["trip"]["title"] == "Porto"
    assert metadata["photos"][0]["analysis"]["user_note"] == "A private photo note."


def _analyzed_trip(client, monkeypatch):
    from backend.app.api.routes import analysis

    fake_client = FakeGemmaClient([_photo_analysis_json("First"), _trip_synthesis_json([1])])
    monkeypatch.setattr(analysis, "get_gemma_client", lambda: fake_client)

    trip = client.post("/api/trips", json={"title": "Porto"}).json()
    photo = _upload_photo(client, trip["id"])
    response = client.post(f"/api/trips/{trip['id']}/analyze")
    assert response.status_code == 202
    assert client.get(f"/api/jobs/{response.json()['id']}").json()["status"] == "completed"
    return trip, photo


def _upload_photo(client, trip_id: int, filename: str = "photo.jpg", color: str = "navy"):
    response = client.post(
        f"/api/trips/{trip_id}/photos",
        files=[("files", (filename, _image_bytes(color), "image/jpeg"))],
    )
    assert response.status_code == 200
    return response.json()[0]


def _image_bytes(color: str) -> bytes:
    image = BytesIO()
    Image.new("RGB", (12, 10), color=color).save(image, format="JPEG")
    return image.getvalue()


def _photo_analysis_json(caption: str = "Blue tiles in afternoon light") -> str:
    return json.dumps(
        {
            "scene_summary": "A tiled street with soft afternoon light.",
            "memory_caption": caption,
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
