"""Integration tests for the Bookmark Manager API.

Each test gets a fresh, seeded SQLite database via the function-scoped
`client` fixture from conftest.py. The 15-bookmark / 3-collection / 10-tag
seed (4 favourites) is the baseline for every test in this module.
"""


# ---------- Bookmarks ----------


def test_create_bookmark(client):
    payload = {
        "url": "https://example.com/article",
        "title": "Example Article",
        "description": "A test bookmark",
        "tags": ["alpha", "beta"],
    }
    resp = client.post("/api/bookmarks", json=payload)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["title"] == "Example Article"
    assert body["url"].startswith("https://example.com/article")
    assert body["description"] == "A test bookmark"
    assert body["is_favourite"] is False
    assert sorted(body["tags"]) == ["alpha", "beta"]
    assert body["id"]


def test_create_bookmark_creates_tags(client):
    payload = {
        "url": "https://example.com/tagged",
        "title": "Tagged",
        "tags": ["brand-new-tag", "python"],
    }
    resp = client.post("/api/bookmarks", json=payload)
    assert resp.status_code == 201

    tags_resp = client.get("/api/tags")
    assert tags_resp.status_code == 200
    tag_names = {t["name"] for t in tags_resp.json()}
    assert "brand-new-tag" in tag_names
    assert "python" in tag_names


def test_list_bookmarks(client):
    resp = client.get("/api/bookmarks", params={"limit": 500})
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) >= 15


def test_list_bookmarks_filter_tag(client):
    resp = client.get("/api/bookmarks", params={"tag": "python", "limit": 500})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) > 0
    for b in body:
        assert "python" in b["tags"]


def test_list_bookmarks_filter_favourite(client):
    resp = client.get(
        "/api/bookmarks",
        params={"is_favourite": "true", "limit": 500},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 4
    for b in body:
        assert b["is_favourite"] is True


def test_list_bookmarks_filter_collection(client):
    cols = client.get("/api/collections").json()
    development = next(c for c in cols if c["name"] == "Development")
    resp = client.get(
        "/api/bookmarks",
        params={"collection_id": development["id"], "limit": 500},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 5
    for b in body:
        assert b["collection_id"] == development["id"]


def test_get_bookmark(client):
    listing = client.get("/api/bookmarks", params={"limit": 1}).json()
    assert listing
    bookmark_id = listing[0]["id"]
    resp = client.get(f"/api/bookmarks/{bookmark_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == bookmark_id


def test_update_bookmark_tags(client):
    create_resp = client.post(
        "/api/bookmarks",
        json={
            "url": "https://example.com/orphan-test",
            "title": "Orphan Test",
            "tags": ["orphan-only-tag", "python"],
        },
    )
    assert create_resp.status_code == 201
    bookmark_id = create_resp.json()["id"]

    tag_names_before = {t["name"] for t in client.get("/api/tags").json()}
    assert "orphan-only-tag" in tag_names_before

    update_resp = client.put(
        f"/api/bookmarks/{bookmark_id}",
        json={"tags": ["new-tag"]},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["tags"] == ["new-tag"]

    tag_names_after = {t["name"] for t in client.get("/api/tags").json()}
    assert "new-tag" in tag_names_after
    assert "orphan-only-tag" not in tag_names_after, "orphaned tag should be cleaned up"
    assert "python" in tag_names_after, "non-orphan tag must remain"


def test_delete_bookmark(client):
    listing = client.get("/api/bookmarks", params={"limit": 1}).json()
    bookmark_id = listing[0]["id"]

    delete_resp = client.delete(f"/api/bookmarks/{bookmark_id}")
    assert delete_resp.status_code == 204

    get_resp = client.get(f"/api/bookmarks/{bookmark_id}")
    assert get_resp.status_code == 404


def test_toggle_favourite(client):
    listing = client.get(
        "/api/bookmarks", params={"is_favourite": "false", "limit": 1}
    ).json()
    assert listing
    bookmark_id = listing[0]["id"]
    assert listing[0]["is_favourite"] is False

    resp = client.post(f"/api/bookmarks/{bookmark_id}/favourite")
    assert resp.status_code == 200
    assert resp.json()["is_favourite"] is True

    resp = client.post(f"/api/bookmarks/{bookmark_id}/favourite")
    assert resp.status_code == 200
    assert resp.json()["is_favourite"] is False


# ---------- Collections ----------


def test_create_collection(client):
    resp = client.post(
        "/api/collections",
        json={"name": "Personal", "description": "My stuff", "color": "#10b981"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Personal"
    assert body["color"] == "#10b981"
    assert body["bookmark_count"] == 0


def test_list_collections_with_count(client):
    resp = client.get("/api/collections")
    assert resp.status_code == 200
    body = resp.json()
    counts = {c["name"]: c["bookmark_count"] for c in body}
    assert counts["Development"] == 5
    assert counts["Design"] == 4
    assert counts["Research"] == 3


def test_delete_collection_nulls_bookmarks(client):
    cols = client.get("/api/collections").json()
    development = next(c for c in cols if c["name"] == "Development")
    collection_id = development["id"]

    listing = client.get(
        "/api/bookmarks",
        params={"collection_id": collection_id, "limit": 500},
    ).json()
    assert len(listing) == 5
    sample_id = listing[0]["id"]

    del_resp = client.delete(f"/api/collections/{collection_id}")
    assert del_resp.status_code == 204

    sample = client.get(f"/api/bookmarks/{sample_id}").json()
    assert sample["collection_id"] is None


# ---------- Search ----------


def test_search_by_title(client):
    resp = client.get("/api/bookmarks/search", params={"q": "FastAPI"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) >= 1
    assert any("FastAPI" in b["title"] for b in body)


def test_search_by_url(client):
    resp = client.get("/api/bookmarks/search", params={"q": "fastapi.tiangolo"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) >= 1
    assert any("fastapi.tiangolo" in b["url"] for b in body)


# ---------- Import / Export ----------


def test_export_import_roundtrip(client):
    export_resp = client.get("/api/bookmarks/export")
    assert export_resp.status_code == 200
    export = export_resp.json()
    original_count = export["count"]
    assert original_count == 15
    original_urls = sorted(b["url"] for b in export["bookmarks"])

    listing = client.get("/api/bookmarks", params={"limit": 500}).json()
    for b in listing:
        del_resp = client.delete(f"/api/bookmarks/{b['id']}")
        assert del_resp.status_code == 204

    after_delete = client.get("/api/bookmarks", params={"limit": 500}).json()
    assert after_delete == []

    import_resp = client.post("/api/bookmarks/import", json=export)
    assert import_resp.status_code == 200
    body = import_resp.json()
    assert body["imported"] == original_count
    assert body["skipped"] == 0

    after = client.get("/api/bookmarks", params={"limit": 500}).json()
    assert len(after) == original_count
    after_urls = sorted(b["url"] for b in after)
    assert after_urls == original_urls


# ---------- General ----------


def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "version": "1.0.0"}


def test_pagination(client):
    first = client.get("/api/bookmarks", params={"limit": 5, "offset": 0}).json()
    assert len(first) == 5

    rest = client.get("/api/bookmarks", params={"limit": 500, "offset": 10}).json()
    assert len(rest) == 5

    first_ids = {b["id"] for b in first}
    rest_ids = {b["id"] for b in rest}
    assert first_ids.isdisjoint(rest_ids)
