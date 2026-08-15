from __future__ import annotations


def test_trip_create_and_list(client):
    create_response = client.post(
        "/api/trips",
        json={"title": "Lisbon Weekend", "description": "Tiles, hills, and seafood."},
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["title"] == "Lisbon Weekend"
    assert created["description"] == "Tiles, hills, and seafood."

    list_response = client.get("/api/trips")
    assert list_response.status_code == 200
    trips = list_response.json()
    assert len(trips) == 1
    assert trips[0]["id"] == created["id"]


def test_missing_trip_detail_returns_404(client):
    response = client.get("/api/trips/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Trip not found"
