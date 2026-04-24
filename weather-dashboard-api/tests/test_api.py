"""Integration tests for the Weather Dashboard API."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


# Seeded city IDs (from app/seed.py)
_CITY_LONDON = "c1a0b1c4-0001-4a1a-8a1a-000000000001"
_CITY_TOKYO = "c1a0b1c4-0002-4a1a-8a1a-000000000002"
_CITY_NEW_YORK = "c1a0b1c4-0003-4a1a-8a1a-000000000003"
_CITY_SYDNEY = "c1a0b1c4-0004-4a1a-8a1a-000000000004"
_CITY_BERLIN = "c1a0b1c4-0005-4a1a-8a1a-000000000005"


def test_health_check(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "version": "1.0.0"}


def test_create_city(client: TestClient) -> None:
    payload = {
        "name": "Paris",
        "country": "FR",
        "latitude": 48.8566,
        "longitude": 2.3522,
    }
    resp = client.post("/api/cities", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Paris"
    assert data["country"] == "FR"
    assert data["latitude"] == 48.8566
    assert data["longitude"] == 2.3522
    assert data["is_favourite"] is False
    assert "id" in data
    assert "created_at" in data


def test_list_cities(client: TestClient) -> None:
    resp = client.get("/api/cities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 5
    names = {c["name"] for c in data}
    assert names == {"London", "Tokyo", "New York", "Sydney", "Berlin"}


def test_list_cities_filter_country(client: TestClient) -> None:
    resp = client.get("/api/cities", params={"country": "JP"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "Tokyo"
    assert data[0]["country"] == "JP"


def test_list_cities_filter_favourite(client: TestClient) -> None:
    resp = client.get("/api/cities", params={"is_favourite": True})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    names = {c["name"] for c in data}
    assert names == {"Tokyo", "Sydney"}
    for city in data:
        assert city["is_favourite"] is True


def test_delete_city_cascades(client: TestClient) -> None:
    # Verify London has weather records before deletion
    history = client.get(f"/api/weather/{_CITY_LONDON}")
    assert history.status_code == 200
    assert len(history.json()) > 0

    resp = client.delete(f"/api/cities/{_CITY_LONDON}")
    assert resp.status_code == 204

    # City should be gone
    get_resp = client.get(f"/api/cities/{_CITY_LONDON}")
    assert get_resp.status_code == 404

    # Weather records should also be gone (cascade)
    history_after = client.get(f"/api/weather/{_CITY_LONDON}")
    assert history_after.status_code == 200
    assert len(history_after.json()) == 0


def test_toggle_favourite(client: TestClient) -> None:
    # London starts as not favourite
    resp = client.post(f"/api/cities/{_CITY_LONDON}/favourite")
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_favourite"] is True

    # Toggle back
    resp2 = client.post(f"/api/cities/{_CITY_LONDON}/favourite")
    assert resp2.status_code == 200
    assert resp2.json()["is_favourite"] is False


def test_city_summary(client: TestClient) -> None:
    resp = client.get(f"/api/cities/{_CITY_TOKYO}/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["city"]["name"] == "Tokyo"
    assert data["record_count"] == 6
    latest = data["latest"]
    assert latest is not None
    assert latest["city_id"] == _CITY_TOKYO
    assert "condition" in latest


def test_record_weather(client: TestClient) -> None:
    payload = {
        "city_id": _CITY_BERLIN,
        "temperature_c": 7.5,
        "humidity": 82,
        "wind_speed_kmh": 21.0,
        "condition": "snowy",
    }
    resp = client.post("/api/weather", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["city_id"] == _CITY_BERLIN
    assert data["temperature_c"] == 7.5
    assert data["humidity"] == 82
    assert data["wind_speed_kmh"] == 21.0
    assert data["condition"] == "snowy"
    assert "id" in data
    assert "recorded_at" in data


def test_record_weather_invalid_city(client: TestClient) -> None:
    payload = {
        "city_id": "non-existent-city-id",
        "temperature_c": 10.0,
        "humidity": 50,
        "wind_speed_kmh": 10.0,
        "condition": "sunny",
    }
    resp = client.post("/api/weather", json=payload)
    assert resp.status_code == 404


def test_weather_history(client: TestClient) -> None:
    resp = client.get(f"/api/weather/{_CITY_NEW_YORK}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 6
    # Verify descending order by recorded_at
    timestamps = [r["recorded_at"] for r in data]
    assert timestamps == sorted(timestamps, reverse=True)


def test_weather_latest(client: TestClient) -> None:
    resp = client.get(f"/api/weather/{_CITY_SYDNEY}/latest")
    assert resp.status_code == 200
    data = resp.json()
    assert data["city_id"] == _CITY_SYDNEY

    # Verify it matches the first record from history
    history = client.get(f"/api/weather/{_CITY_SYDNEY}", params={"limit": 1})
    assert history.status_code == 200
    assert history.json()[0]["id"] == data["id"]


def test_weather_pagination(client: TestClient) -> None:
    # Default limit should return all 6 seeded records
    resp = client.get(f"/api/weather/{_CITY_BERLIN}")
    assert resp.status_code == 200
    assert len(resp.json()) == 6

    # Limit to 2
    resp2 = client.get(f"/api/weather/{_CITY_BERLIN}", params={"limit": 2})
    assert resp2.status_code == 200
    assert len(resp2.json()) == 2

    # Offset 2, limit 2
    resp3 = client.get(f"/api/weather/{_CITY_BERLIN}", params={"limit": 2, "offset": 2})
    assert resp3.status_code == 200
    assert len(resp3.json()) == 2

    # Offset beyond data
    resp4 = client.get(f"/api/weather/{_CITY_BERLIN}", params={"offset": 100})
    assert resp4.status_code == 200
    assert resp4.json() == []


def test_get_city_not_found(client: TestClient) -> None:
    resp = client.get("/api/cities/does-not-exist")
    assert resp.status_code == 404


def test_delete_city_not_found(client: TestClient) -> None:
    resp = client.delete("/api/cities/does-not-exist")
    assert resp.status_code == 404


def test_create_city_duplicate(client: TestClient) -> None:
    payload = {
        "name": "Tokyo",
        "country": "JP",
        "latitude": 35.6762,
        "longitude": 139.6503,
    }
    resp = client.post("/api/cities", json=payload)
    assert resp.status_code == 409
