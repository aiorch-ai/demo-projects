"""Smoke tests for the FastAPI app and route layer."""

import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path):
    """Function-scoped fixture: fresh DB per test, lifespan triggered via TestClient."""
    db_file = tmp_path / "test.db"
    old = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = f"sqlite:///{db_file}"
    try:
        from app.main import app

        with TestClient(app) as c:
            yield c
    finally:
        if old is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = old


def test_health_returns_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "version": "1.0.0"}


def test_create_bookmark_returns_201_with_tags(client):
    payload = {
        "url": "https://example.com/article",
        "title": "Example Article",
        "description": "A test bookmark",
        "tags": ["test", "smoke", "test"],
    }
    resp = client.post("/api/bookmarks", json=payload)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["title"] == "Example Article"
    assert body["url"].startswith("https://example.com/article")
    assert body["is_favourite"] is False
    assert sorted(body["tags"]) == ["smoke", "test"]
    assert body["id"]


def test_list_collections_returns_seeded_with_counts(client):
    resp = client.get("/api/collections")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) == 3
    for entry in body:
        assert "bookmark_count" in entry
        assert isinstance(entry["bookmark_count"], int)
    counts_by_name = {c["name"]: c["bookmark_count"] for c in body}
    assert counts_by_name["Development"] == 5
    assert counts_by_name["Design"] == 4
    assert counts_by_name["Research"] == 3
