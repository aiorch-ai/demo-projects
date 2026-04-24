from __future__ import annotations

from fastapi.testclient import TestClient


def test_create_contact(client: TestClient) -> None:
    payload = {
        "name": "Alice Smith",
        "email": "alice@example.com",
        "phone": "555-1234",
        "company": "Acme Corp",
        "notes": "Friend from college",
    }
    response = client.post("/contacts", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["email"] == payload["email"]
    assert data["phone"] == payload["phone"]
    assert data["company"] == payload["company"]
    assert data["notes"] == payload["notes"]
    assert "id" in data
    assert data["id"]
    assert "created_at" in data
    assert "updated_at" in data
    assert data["created_at"]
    assert data["updated_at"]


def test_create_contact_missing_name(client: TestClient) -> None:
    payload = {"email": "no-name@example.com"}
    response = client.post("/contacts", json=payload)
    assert response.status_code == 422


def test_list_contacts_empty(client: TestClient) -> None:
    response = client.get("/contacts")
    assert response.status_code == 200
    assert response.json() == []


def test_list_contacts_sorted(client: TestClient) -> None:
    names = ["Charlie", "Alice", "Bob"]
    for name in names:
        resp = client.post("/contacts", json={"name": name})
        assert resp.status_code == 201
    response = client.get("/contacts")
    assert response.status_code == 200
    data = response.json()
    assert [c["name"] for c in data] == ["Alice", "Bob", "Charlie"]


def test_get_contact_hit(client: TestClient) -> None:
    create_resp = client.post("/contacts", json={"name": "Diana", "email": "diana@example.com"})
    assert create_resp.status_code == 201
    created = create_resp.json()
    response = client.get(f"/contacts/{created['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created["id"]
    assert data["name"] == "Diana"
    assert data["email"] == "diana@example.com"


def test_get_contact_miss(client: TestClient) -> None:
    response = client.get("/contacts/nonexistent-id")
    assert response.status_code == 404


def test_update_contact_partial(client: TestClient) -> None:
    create_resp = client.post("/contacts", json={"name": "Eve", "email": "eve@old.com"})
    assert create_resp.status_code == 201
    created = create_resp.json()
    response = client.put(f"/contacts/{created['id']}", json={"email": "eve@new.com"})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created["id"]
    assert data["name"] == "Eve"
    assert data["email"] == "eve@new.com"


def test_update_contact_missing(client: TestClient) -> None:
    response = client.put("/contacts/nonexistent-id", json={"email": "new@example.com"})
    assert response.status_code == 404


def test_delete_contact_existing(client: TestClient) -> None:
    create_resp = client.post("/contacts", json={"name": "Frank"})
    assert create_resp.status_code == 201
    created = create_resp.json()
    response = client.delete(f"/contacts/{created['id']}")
    assert response.status_code == 204
    get_resp = client.get(f"/contacts/{created['id']}")
    assert get_resp.status_code == 404


def test_delete_contact_missing(client: TestClient) -> None:
    response = client.delete("/contacts/nonexistent-id")
    assert response.status_code == 404


def test_search_contacts_case_insensitive(client: TestClient) -> None:
    client.post("/contacts", json={"name": "Alice Wonderland"})
    client.post("/contacts", json={"name": "Bob Builder"})
    client.post("/contacts", json={"name": "alice smith"})
    response = client.get("/contacts/search", params={"q": "alice"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert {c["name"] for c in data} == {"Alice Wonderland", "alice smith"}


def test_search_contacts_empty_query(client: TestClient) -> None:
    response = client.get("/contacts/search", params={"q": ""})
    assert response.status_code == 200
    assert response.json() == []
