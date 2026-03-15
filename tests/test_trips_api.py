"""
Trips API tests. Use the test DB from conftest (no real data).
"""
from fastapi.testclient import TestClient


def test_list_trips_empty(client: TestClient):
    """GET /api/trips returns 200 and empty list when no trips."""
    r = client.get("/api/trips")
    assert r.status_code == 200
    assert r.json() == {"trips": []}


def test_create_and_get_trip(client: TestClient):
    """POST /api/trips creates a trip; GET /api/trips/{id} returns it with empty price_events."""
    r = client.post(
        "/api/trips",
        json={
            "origin": "Madrid",
            "destination": "Zaragoza",
            "date": "2025-06-15",
            "train_identifier": "AVE 0101",
            "check_interval_minutes": 60,
        },
    )
    assert r.status_code == 200
    trip = r.json()
    assert trip["origin"] == "Madrid"
    assert trip["destination"] == "Zaragoza"
    assert "id" in trip

    r2 = client.get(f"/api/trips/{trip['id']}")
    assert r2.status_code == 200
    data = r2.json()
    assert data["trip"]["id"] == trip["id"]
    assert data["price_events"] == []
