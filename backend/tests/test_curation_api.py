from __future__ import annotations

import json
from io import BytesIO
from typing import Any, Mapping, Sequence

from PIL import Image
from pydantic import BaseModel
from sqlmodel import Session


class FakeGemmaClient:
    def __init__(self, responses: list[str]) -> None:
        self.responses = responses

    def complete_json(
        self,
        *,
        messages: Sequence[Mapping[str, Any]],
        schema: type[BaseModel],
        options: Mapping[str, Any],
    ) -> str:
        if not self.responses:
            raise AssertionError("No fake Gemma response queued")
        return self.responses.pop(0)


def test_trip_patch_sets_cover_and_validates_trip_ownership(client):
    first_trip = client.post("/api/trips", json={"title": "Porto"}).json()
    second_trip = client.post("/api/trips", json={"title": "Lisbon"}).json()
    first_photo = _upload_photo(client, first_trip["id"])
    second_photo = _upload_photo(client, second_trip["id"])

    response = client.patch(
        f"/api/trips/{first_trip['id']}",
        json={
            "title": "Porto Weekend",
            "description": None,
            "cover_photo_id": first_photo["id"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "Porto Weekend"
    assert payload["description"] is None
    assert payload["cover_photo_id"] == first_photo["id"]

    invalid_response = client.patch(
        f"/api/trips/{first_trip['id']}",
        json={"cover_photo_id": second_photo["id"]},
    )
    assert invalid_response.status_code == 400
    assert invalid_response.json()["detail"] == "Cover photo must belong to this trip"


def test_photo_favorite_and_memory_overrides_survive_analysis_rerun(client, monkeypatch):
    trip, photo = _analyzed_trip(client, monkeypatch)

    response = client.patch(
        f"/api/photos/{photo['id']}",
        json={
            "is_favorite": True,
            "user_memory_caption": "My favorite tile corner",
            "user_scene_summary": "A corner I remember clearly.",
            "user_mood": "nostalgic",
            "user_note": "This was right after lunch.",
        },
    )

    assert response.status_code == 200
    updated = response.json()
    assert updated["is_favorite"] is True
    assert updated["analysis"]["memory_caption"] == "My favorite tile corner"
    assert updated["analysis"]["scene_summary"] == "A corner I remember clearly."
    assert updated["analysis"]["user_mood"] == "nostalgic"
    assert (
        updated["analysis"]["raw_model_json"]["photo_memory"]["memory_caption"]
        == "Blue tiles in afternoon light"
    )

    _rerun_analysis(client, monkeypatch, trip["id"], photo["id"])
    detail = client.get(f"/api/trips/{trip['id']}").json()
    rerun_photo = detail["photos"][0]
    assert rerun_photo["is_favorite"] is True
    assert rerun_photo["analysis"]["memory_caption"] == "My favorite tile corner"
    assert (
        rerun_photo["analysis"]["raw_model_json"]["photo_memory"]["memory_caption"]
        == "Second generated caption"
    )

    reset = client.patch(
        f"/api/photos/{photo['id']}",
        json={"is_favorite": False, "user_memory_caption": None},
    )
    assert reset.status_code == 200
    assert reset.json()["is_favorite"] is False
    assert reset.json()["analysis"]["memory_caption"] == "Second generated caption"


def test_photo_memory_edit_requires_analysis(client):
    trip = client.post("/api/trips", json={"title": "Porto"}).json()
    photo = _upload_photo(client, trip["id"])

    response = client.patch(
        f"/api/photos/{photo['id']}",
        json={"user_memory_caption": "Before analysis"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Analyze this photo before editing memory"


def test_trip_memory_override_and_markdown_export(client, monkeypatch):
    trip, photo = _analyzed_trip(client, monkeypatch)

    from backend.app.db.models import Photo
    from backend.app.db.session import get_engine

    with Session(get_engine()) as session:
        record = session.get(Photo, photo["id"])
        record.latitude = 41.1579
        record.longitude = -8.6291
        session.add(record)
        session.commit()

    client.patch(
        f"/api/photos/{photo['id']}",
        json={
            "is_favorite": True,
            "user_memory_caption": "My favorite tile corner",
            "user_note": "A small personal note.",
        },
    )
    response = client.patch(
        f"/api/trips/{trip['id']}/memory",
        json={
            "user_narrative_summary": "A more personal Porto memory.",
            "user_note": "Keep this one private.",
        },
    )

    assert response.status_code == 200
    assert response.json()["user_narrative_summary"] == "A more personal Porto memory."

    export_response = client.get(f"/api/trips/{trip['id']}/export.md")
    assert export_response.status_code == 200
    assert export_response.headers["content-type"].startswith("text/markdown")
    body = export_response.text
    assert "# Porto" in body
    assert "A more personal Porto memory." in body
    assert "Keep this one private." in body
    assert "My favorite tile corner" in body
    assert "A small personal note." in body
    assert "Evidence photos: #1" in body
    assert "GPS: 41.1579, -8.6291" in body
    assert "- Kept: yes" in body


def test_trip_memory_edit_requires_memory(client):
    trip = client.post("/api/trips", json={"title": "No memory"}).json()

    response = client.patch(
        f"/api/trips/{trip['id']}/memory",
        json={"user_narrative_summary": "Not yet"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Analyze this trip before editing trip memory"


def _analyzed_trip(client, monkeypatch):
    from backend.app.api.routes import analysis

    fake_client = FakeGemmaClient([_photo_analysis_json(), _trip_synthesis_json([1])])
    monkeypatch.setattr(analysis, "get_gemma_client", lambda: fake_client)

    trip = client.post("/api/trips", json={"title": "Porto"}).json()
    photo = _upload_photo(client, trip["id"])
    response = client.post(f"/api/trips/{trip['id']}/analyze")
    assert response.status_code == 202
    assert client.get(f"/api/jobs/{response.json()['id']}").json()["status"] == "completed"
    return trip, photo


def _rerun_analysis(client, monkeypatch, trip_id: int, photo_id: int) -> None:
    from backend.app.api.routes import analysis

    fake_client = FakeGemmaClient(
        [_photo_analysis_json("Second generated caption"), _trip_synthesis_json([photo_id])]
    )
    monkeypatch.setattr(analysis, "get_gemma_client", lambda: fake_client)
    response = client.post(f"/api/trips/{trip_id}/analyze")
    assert response.status_code == 202
    assert client.get(f"/api/jobs/{response.json()['id']}").json()["status"] == "completed"


def _upload_photo(client, trip_id: int):
    response = client.post(
        f"/api/trips/{trip_id}/photos",
        files=[("files", ("porto.jpg", _image_bytes(), "image/jpeg"))],
    )
    assert response.status_code == 200
    return response.json()[0]


def _image_bytes() -> bytes:
    image = BytesIO()
    Image.new("RGB", (12, 10), color="navy").save(image, format="JPEG")
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
