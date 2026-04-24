"""Integration tests for the Snippet Vault API."""
from __future__ import annotations

from fastapi.testclient import TestClient


_SNIPPET_FIBONACCI = "61ef6f34-4f0d-4bc0-8c89-c1d7e6c9d101"
_SNIPPET_FASTAPI = "84e0c762-1b35-4ea0-b8c4-0762cb6d6d02"
_SNIPPET_FETCH_JSON = "f3adb7e0-7c6e-4dc2-a585-1ce9ec5af603"
_SNIPPET_DEBOUNCE = "8f6db5df-2f39-45d4-8d36-08b06595d904"
_SNIPPET_GO_HEALTH = "2d917cd3-7a60-4b56-9367-52a88bca2b05"
_SNIPPET_WORKER_POOL = "b65abf03-afda-4f8c-b4a5-4a7068352b06"
_SNIPPET_TOP_ORDERS = "4bd590b6-1bba-491f-b13a-bc7a73c94907"
_SNIPPET_TAG_UPSERT = "c03415d2-d4bb-4f35-a4eb-4ca8d5fbe808"
_SNIPPET_ROTATE_LOGS = "9a8f4b77-9d5f-4d3b-b15c-557b2c4dcb09"
_SNIPPET_WAIT_READY = "cb8d0cd4-8cb0-4cb8-8b7f-9d26c2105810"


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "1.0.0"}


def test_create_snippet(client: TestClient) -> None:
    payload = {
        "title": "Parse env file",
        "code": "def parse_env(text: str) -> dict[str, str]:\n    return {}\n",
        "language": "python",
        "description": "Utility for loading KEY=value pairs.",
        "tags": ["utility", "parser"],
        "is_public": False,
    }
    response = client.post("/api/snippets", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["language"] == "python"
    assert data["description"] == payload["description"]
    assert data["is_public"] is False
    assert data["view_count"] == 0
    assert data["tags"] == ["parser", "utility"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_snippet_creates_tags(client: TestClient) -> None:
    payload = {
        "title": "Build response headers",
        "code": "const headers = new Headers();",
        "language": "javascript",
        "tags": ["http", "edge-cache", "http"],
        "is_public": True,
    }

    response = client.post("/api/snippets", json=payload)
    assert response.status_code == 201
    assert response.json()["tags"] == ["edge-cache", "http"]

    tags_response = client.get("/api/tags")
    assert tags_response.status_code == 200
    tags = {tag["name"]: tag["snippet_count"] for tag in tags_response.json()}
    assert tags["http"] == 1
    assert tags["edge-cache"] == 1


def test_list_snippets(client: TestClient) -> None:
    response = client.get("/api/snippets")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 10
    assert data[0]["id"] == _SNIPPET_WAIT_READY
    assert data[-1]["id"] == _SNIPPET_FIBONACCI
    assert all(isinstance(item["is_public"], bool) for item in data)
    assert all(isinstance(item["tags"], list) for item in data)


def test_list_snippets_filter_language(client: TestClient) -> None:
    response = client.get("/api/snippets", params={"language": "python"})
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 2
    assert {item["id"] for item in data} == {_SNIPPET_FIBONACCI, _SNIPPET_FASTAPI}
    assert {item["language"] for item in data} == {"python"}


def test_list_snippets_filter_tag(client: TestClient) -> None:
    response = client.get("/api/snippets", params={"tag": "api"})
    assert response.status_code == 200

    data = response.json()
    assert {item["id"] for item in data} == {
        _SNIPPET_FASTAPI,
        _SNIPPET_FETCH_JSON,
        _SNIPPET_GO_HEALTH,
        _SNIPPET_TAG_UPSERT,
    }


def test_list_snippets_filter_public(client: TestClient) -> None:
    response = client.get("/api/snippets", params={"is_public": False})
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 3
    assert {item["id"] for item in data} == {
        _SNIPPET_DEBOUNCE,
        _SNIPPET_WORKER_POOL,
        _SNIPPET_TAG_UPSERT,
    }
    assert all(item["is_public"] is False for item in data)


def test_get_snippet_increments_views(client: TestClient) -> None:
    first = client.get(f"/api/snippets/{_SNIPPET_FIBONACCI}")
    assert first.status_code == 200
    assert first.json()["view_count"] == 19

    second = client.get(f"/api/snippets/{_SNIPPET_FIBONACCI}")
    assert second.status_code == 200
    assert second.json()["view_count"] == 20


def test_update_snippet_tags(client: TestClient) -> None:
    payload = {
        "title": "Rotate logs older than thirty days",
        "tags": ["ops", "shell", "ops"],
        "is_public": False,
    }

    response = client.put(f"/api/snippets/{_SNIPPET_ROTATE_LOGS}", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["title"] == payload["title"]
    assert data["is_public"] is False
    assert data["tags"] == ["ops", "shell"]

    filtered = client.get("/api/snippets", params={"tag": "devops"})
    assert filtered.status_code == 200
    assert _SNIPPET_ROTATE_LOGS not in {item["id"] for item in filtered.json()}


def test_delete_snippet(client: TestClient) -> None:
    delete_response = client.delete(f"/api/snippets/{_SNIPPET_FASTAPI}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/api/snippets/{_SNIPPET_FASTAPI}")
    assert get_response.status_code == 404

    tag_response = client.get("/api/snippets", params={"tag": "utility"})
    assert tag_response.status_code == 200
    assert _SNIPPET_FASTAPI not in {item["id"] for item in tag_response.json()}


def test_search_by_title(client: TestClient) -> None:
    response = client.get("/api/snippets/search", params={"q": "fibonacci"})
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == _SNIPPET_FIBONACCI


def test_search_by_code(client: TestClient) -> None:
    response = client.get("/api/snippets/search", params={"q": "ROW_NUMBER"})
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == _SNIPPET_TOP_ORDERS


def test_search_with_language_filter(client: TestClient) -> None:
    response = client.get(
        "/api/snippets/search",
        params={"q": "handler", "language": "go"},
    )
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == _SNIPPET_GO_HEALTH


def test_language_stats(client: TestClient) -> None:
    response = client.get("/api/stats/languages")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 5
    counts = {row["language"]: row["snippet_count"] for row in data}
    assert counts == {
        "bash": 2,
        "go": 2,
        "javascript": 2,
        "python": 2,
        "sql": 2,
    }


def test_popular_snippets(client: TestClient) -> None:
    response = client.get("/api/stats/popular")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 5
    assert [item["id"] for item in data] == [
        _SNIPPET_TOP_ORDERS,
        _SNIPPET_FETCH_JSON,
        _SNIPPET_WAIT_READY,
        _SNIPPET_WORKER_POOL,
        _SNIPPET_FIBONACCI,
    ]


def test_list_tags(client: TestClient) -> None:
    response = client.get("/api/tags")
    assert response.status_code == 200

    data = response.json()
    tags = {row["name"]: row["snippet_count"] for row in data}
    assert tags["algorithm"] == 1
    assert tags["api"] == 4
    assert tags["utility"] == 4


def test_delete_tag_removes_association_from_snippets(client: TestClient) -> None:
    delete_response = client.delete("/api/tags/api")
    assert delete_response.status_code == 204

    tags_response = client.get("/api/tags")
    assert tags_response.status_code == 200
    assert "api" not in {tag["name"] for tag in tags_response.json()}

    snippets_response = client.get("/api/snippets", params={"tag": "api"})
    assert snippets_response.status_code == 200
    assert snippets_response.json() == []
