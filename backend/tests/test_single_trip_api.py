from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

from PIL import Image
from sqlmodel import Session

from backend.tests.test_curation_api import (
    FakeGemmaClient,
    _photo_analysis_json,
    _trip_synthesis_json,
)


def test_import_auto_starts_analysis(client, monkeypatch):
    _enable_auto_analyze(monkeypatch)
    from backend.app.api.routes import analysis

    monkeypatch.setattr(
        analysis,
        "get_gemma_client",
        lambda: FakeGemmaClient([_photo_analysis_json(), _trip_synthesis_json([1])]),
    )

    trip = client.post("/api/trips", json={"title": "Bahamas"}).json()
    payload = _import_photo(client, trip["id"])

    assert payload["stored_count"] == 1
    assert payload["job"] is not None
    assert payload["job"]["mode"] == "missing"

    # TestClient runs background tasks synchronously once the response is sent.
    job = client.get(f"/api/jobs/{payload['job']['id']}").json()
    assert job["status"] == "completed"

    photo = client.get(f"/api/trips/{trip['id']}").json()["photos"][0]
    assert photo["analysis"]["memory_caption"] == "Blue tiles in afternoon light"


def test_import_without_auto_analyze_returns_no_job(client):
    trip = client.post("/api/trips", json={"title": "Bahamas"}).json()
    payload = _import_photo(client, trip["id"])

    assert payload["stored_count"] == 1
    assert payload["job"] is None


def test_second_import_joins_the_running_job(client, monkeypatch):
    _enable_auto_analyze(monkeypatch)
    from backend.app.api.routes import analysis
    from backend.app.db.models import AnalysisJob
    from backend.app.db.session import get_engine

    monkeypatch.setattr(analysis, "get_gemma_client", lambda: FakeGemmaClient([]))

    trip = client.post("/api/trips", json={"title": "Bahamas"}).json()
    first = _import_photo(client, trip["id"], name="one.jpg", color="navy")

    # Force the job back to running so the second import sees it as in flight.
    with Session(get_engine()) as session:
        job = session.get(AnalysisJob, first["job"]["id"])
        job.status = "running"
        session.add(job)
        session.commit()

    second = _import_photo(client, trip["id"], name="two.jpg", color="teal")

    assert second["job"]["id"] == first["job"]["id"]


def test_delete_all_photos_keeps_trip(client, monkeypatch):
    from backend.app.core.config import get_settings

    trip = client.post("/api/trips", json={"title": "Bahamas"}).json()
    photo = _import_photo(client, trip["id"])["results"][0]["photo"]
    client.patch(f"/api/trips/{trip['id']}", json={"cover_photo_id": photo["id"]})
    client.patch(
        f"/api/photos/{photo['id']}", json={"user_memory_caption": "A caption"}
    )

    stored = Path(get_settings().upload_dir) / photo["stored_path"]
    assert stored.exists()

    response = client.delete(f"/api/trips/{trip['id']}/photos")
    assert response.status_code == 204
    assert not stored.exists()

    detail = client.get(f"/api/trips/{trip['id']}").json()
    assert detail["photos"] == []
    assert detail["memory"] is None
    assert detail["cover_photo_id"] is None


def _enable_auto_analyze(monkeypatch) -> None:
    from backend.app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "auto_analyze_on_import", True)


def _import_photo(client, trip_id: int, name: str = "porto.jpg", color: str = "navy"):
    response = client.post(
        f"/api/trips/{trip_id}/photos/import",
        files=[("files", (name, _image_bytes(color), "image/jpeg"))],
    )
    assert response.status_code == 200
    return response.json()


def _image_bytes(color: str = "navy") -> bytes:
    image = BytesIO()
    Image.new("RGB", (12, 10), color=color).save(image, format="JPEG")
    return image.getvalue()
