"""
Search API tests. GTFS backend is mocked so tests don't call the real Renfe lib.
"""
from unittest.mock import patch

from fastapi.testclient import TestClient


def test_search_options_includes_zaragoza_calatayud_tafalla(client: TestClient):
    """GET /api/search/options must include Zaragoza, Calatayud, Tafalla."""
    r = client.get("/api/search/options")
    assert r.status_code == 200
    data = r.json()
    origins = data.get("origins", [])
    destinations = data.get("destinations", [])
    for name in ("Zaragoza", "Calatayud", "Tafalla"):
        assert name in origins, f"Missing origin: {name}"
        assert name in destinations, f"Missing destination: {name}"


def test_search_returns_trains_when_backend_mocked(client: TestClient):
    """POST /api/search returns 200 and trains when GTFS backend returns data (mocked)."""
    mock_trains = [
        {"name": "AVE 0101", "price": 45.50, "duration_minutes": 90, "estimated_price_min": None, "estimated_price_max": None},
    ]
    with patch("app.api.search._is_mock_enabled", return_value=False):
        with patch("app.api.search._trains_from_gtfs_backend", return_value=mock_trains):
            r = client.post(
                "/api/search",
                json={"date": "2025-06-15", "origin": "Madrid", "destination": "Zaragoza"},
            )
    assert r.status_code == 200
    data = r.json()
    assert "trains" in data
    assert len(data["trains"]) == 1
    assert data["trains"][0]["name"] == "AVE 0101"
    assert data["trains"][0]["price"] == 45.50


def test_search_returns_503_when_backend_fails(client: TestClient):
    """POST /api/search returns 503 when GTFS backend raises an exception."""
    with patch("app.api.search._is_mock_enabled", return_value=False):
        with patch("app.api.search._trains_from_gtfs_backend", side_effect=Exception("No se pudo conectar con Renfe")):
            r = client.post(
                "/api/search",
                json={"date": "2025-06-15", "origin": "Madrid", "destination": "Barcelona"},
            )
    assert r.status_code == 503
    assert "detail" in r.json()
    assert "Renfe" in r.json()["detail"]
