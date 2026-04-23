"""Integration tests for the Bookmark Manager API — all exercise HTTP routes."""
from __future__ import annotations


DEV_COLLECTION_ID = "a1f0c2d4-0001-4a1a-8a1a-000000000001"


def _list_bookmarks(client, **params):
    resp = client.get("/api/bookmarks", params=params)
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["version"] == "1.0.0"


def test_create_bookmark(client):
    payload = {
        "url": "https://example.com/article",
        "title": "Example Article",
        "description": "An article",
        "tags": ["python", "example"],
    }
    resp = client.post("/api/bookmarks", json=payload)
    assert resp.status_code in (200, 201), resp.text
    body = resp.json()
    assert body["title"] == "Example Article"
    assert sorted(body["tags"]) == ["example", "python"]
    assert body["is_favourite"] is False
    assert body["id"]


def test_create_bookmark_creates_tags(client):
    new_tag = "brand-new-tag-xyz"
    resp = client.post(
        "/api/bookmarks",
        json={
            "url": "https://example.com/new-tag",
            "title": "Has a new tag",
            "tags": [new_tag],
        },
    )
    assert resp.status_code in (200, 201), resp.text

    tags_resp = client.get("/api/tags")
    assert tags_resp.status_code == 200
    tag_names = {t["name"] for t in tags_resp.json()}
    assert new_tag in tag_names


def test_list_bookmarks(client):
    body = _list_bookmarks(client, limit=100)
    assert isinstance(body, list)
    assert len(body) >= 15


def test_list_bookmarks_filter_tag(client):
    body = _list_bookmarks(client, tag="python", limit=100)
    assert len(body) >= 1
    for bm in body:
        assert "python" in bm["tags"]


def test_list_bookmarks_filter_favourite(client):
    body = _list_bookmarks(client, is_favourite="true", limit=100)
    assert len(body) >= 1
    for bm in body:
        assert bm["is_favourite"] is True


def test_list_bookmarks_filter_collection(client):
    body = _list_bookmarks(client, collection_id=DEV_COLLECTION_ID, limit=100)
    assert len(body) == 5
    for bm in body:
        assert bm["collection_id"] == DEV_COLLECTION_ID


def test_get_bookmark(client):
    listing = _list_bookmarks(client, limit=1)
    assert listing
    bookmark_id = listing[0]["id"]
    resp = client.get(f"/api/bookmarks/{bookmark_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == bookmark_id
    assert "tags" in body


def test_update_bookmark_tags(client):
    listing = _list_bookmarks(client, limit=1)
    bookmark_id = listing[0]["id"]
    resp = client.put(
        f"/api/bookmarks/{bookmark_id}",
        json={"tags": ["replaced-tag"]},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["tags"] == ["replaced-tag"]


def test_delete_bookmark(client):
    listing = _list_bookmarks(client, limit=1)
    bookmark_id = listing[0]["id"]
    resp = client.delete(f"/api/bookmarks/{bookmark_id}")
    assert resp.status_code in (200, 204)
    resp2 = client.get(f"/api/bookmarks/{bookmark_id}")
    assert resp2.status_code == 404


def test_toggle_favourite(client):
    listing = _list_bookmarks(client, limit=100)
    not_fav = next(bm for bm in listing if not bm["is_favourite"])
    bookmark_id = not_fav["id"]
    resp = client.post(f"/api/bookmarks/{bookmark_id}/favourite")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["is_favourite"] is True

    resp2 = client.post(f"/api/bookmarks/{bookmark_id}/favourite")
    assert resp2.status_code == 200
    assert resp2.json()["is_favourite"] is False


def test_create_collection(client):
    resp = client.post(
        "/api/collections",
        json={"name": "Reading List", "description": "Later", "color": "#10b981"},
    )
    assert resp.status_code in (200, 201), resp.text
    body = resp.json()
    assert body["name"] == "Reading List"
    assert body["color"] == "#10b981"
    assert body["bookmark_count"] == 0


def test_list_collections_with_count(client):
    resp = client.get("/api/collections")
    assert resp.status_code == 200
    body = resp.json()
    dev = next(c for c in body if c["id"] == DEV_COLLECTION_ID)
    assert dev["bookmark_count"] == 5


def test_delete_collection_nulls_bookmarks(client):
    before = _list_bookmarks(client, collection_id=DEV_COLLECTION_ID, limit=100)
    assert len(before) == 5

    resp = client.delete(f"/api/collections/{DEV_COLLECTION_ID}")
    assert resp.status_code in (200, 204), resp.text

    after_filter = _list_bookmarks(client, collection_id=DEV_COLLECTION_ID, limit=100)
    assert after_filter == []

    # The 5 bookmarks should still exist with collection_id=None.
    all_bookmarks = _list_bookmarks(client, limit=100)
    nulled = [bm for bm in all_bookmarks if bm["collection_id"] is None]
    assert len(nulled) >= 5


def test_search_by_title(client):
    resp = client.get("/api/bookmarks/search", params={"q": "python"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert isinstance(body, list)
    assert any(
        "python" in (bm["title"] or "").lower()
        or "python" in (bm["description"] or "").lower()
        or "python" in (bm["url"] or "").lower()
        for bm in body
    )


def test_search_by_url(client):
    resp = client.get("/api/bookmarks/search", params={"q": "github.com"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) >= 1
    assert any("github.com" in bm["url"] for bm in body)


def test_export_import_roundtrip(client):
    export_resp = client.get("/api/bookmarks/export")
    assert export_resp.status_code == 200, export_resp.text
    exported = export_resp.json()
    original_count = exported["count"]
    assert original_count >= 15
    assert len(exported["bookmarks"]) == original_count

    # Delete all bookmarks.
    all_bookmarks = _list_bookmarks(client, limit=500)
    for bm in all_bookmarks:
        del_resp = client.delete(f"/api/bookmarks/{bm['id']}")
        assert del_resp.status_code in (200, 204)

    assert _list_bookmarks(client, limit=500) == []

    # Import the export payload.
    import_resp = client.post("/api/bookmarks/import", json=exported)
    assert import_resp.status_code == 200, import_resp.text
    result = import_resp.json()
    assert result["imported"] == original_count
    assert result["skipped"] == 0

    restored = _list_bookmarks(client, limit=500)
    assert len(restored) == original_count


def test_pagination(client):
    page1 = _list_bookmarks(client, limit=5, offset=0)
    page2 = _list_bookmarks(client, limit=5, offset=5)
    assert len(page1) == 5
    assert len(page2) == 5
    ids1 = {bm["id"] for bm in page1}
    ids2 = {bm["id"] for bm in page2}
    assert ids1.isdisjoint(ids2)
