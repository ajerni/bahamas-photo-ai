from __future__ import annotations

from io import BytesIO

import pytest
from PIL import Image

from backend.app.services.storage import ImageValidationError, normalize_stored_path


def test_uploaded_photo_is_served_from_uploads_route(client):
    trip = client.post("/api/trips", json={"title": "Kyoto"}).json()
    image = _image_bytes()
    photo = client.post(
        f"/api/trips/{trip['id']}/photos",
        files=[("files", ("temple.jpg", image, "image/jpeg"))],
    ).json()[0]

    response = client.get(photo["image_url"])

    assert response.status_code == 200
    assert response.content == image
    assert response.headers["content-type"].startswith("image/jpeg")


def test_stored_path_rejects_parent_segments():
    with pytest.raises(ImageValidationError):
        normalize_stored_path("../secrets.txt")
    with pytest.raises(ImageValidationError):
        normalize_stored_path("trip_1/../../etc/passwd")


def test_uploads_route_returns_404_for_missing_photo(client):
    response = client.get("/uploads/trip_1/missing.jpg")
    assert response.status_code == 404


def _image_bytes() -> bytes:
    image = BytesIO()
    Image.new("RGB", (8, 8), color="red").save(image, format="JPEG")
    return image.getvalue()
