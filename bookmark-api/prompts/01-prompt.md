# Orchestrator Prompt — Bookmark Manager API

Read the task file: `/opt/orchestrator/v3/sample_tasks/bookmark-api/task.md`

## Delivery Principals

- No hardcoding — all configuration from environment variables
- No fallbacks — fail explicitly if DATABASE_URL is not set
- No mock data — seed data must be realistic bookmarks to real websites
- All Pydantic models must use v2 syntax
- Use uuid4 for all primary keys (stored as TEXT in SQLite)
- Seed data must be idempotent (INSERT OR IGNORE)
- All tests must pass: `pytest tests/ -v`

## Pre-Existing Infrastructure

Greenfield project. The git repo at `/opt/demo-bookmark-api` has only a README.md on the `main` branch.

## What to Build

### Agent 1 — Database, Models, Seed Data

**`app/__init__.py`** — empty

**`app/database.py`** — SQLite connection manager:
- Read `DATABASE_URL` from `os.environ` — no default, raise RuntimeError if missing
- WAL mode, busy_timeout=5000, foreign_keys=ON
- `init_db()` creates tables, `get_db()` yields connection with row_factory=sqlite3.Row

**`app/models.py`** — Pydantic v2 models:
- `BookmarkCreate(url: str, title: str, description: str | None, collection_id: str | None, tags: list[str] = [])` — url validated as HttpUrl
- `BookmarkResponse(id, url, title, description, collection_id, tags: list[str], is_favourite: bool, created_at, updated_at)`
- `BookmarkUpdate(title: str | None, description: str | None, collection_id: str | None, is_favourite: bool | None, tags: list[str] | None)`
- `CollectionCreate(name: str, description: str | None, color: str = "#3b82f6")` — color is a hex code for UI display
- `CollectionResponse(id, name, description, color, bookmark_count: int, created_at)`
- `TagResponse(name: str, bookmark_count: int)`
- `BookmarkExport(bookmarks: list[BookmarkResponse], exported_at: str, count: int)`

**Database schema** (4 tables):
```sql
CREATE TABLE IF NOT EXISTS collections (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    color TEXT NOT NULL DEFAULT '#3b82f6',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS bookmarks (
    id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    collection_id TEXT REFERENCES collections(id) ON DELETE SET NULL,
    is_favourite INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tags (
    name TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS bookmark_tags (
    bookmark_id TEXT NOT NULL REFERENCES bookmarks(id) ON DELETE CASCADE,
    tag_name TEXT NOT NULL REFERENCES tags(name) ON DELETE CASCADE,
    PRIMARY KEY (bookmark_id, tag_name)
);

CREATE INDEX IF NOT EXISTS idx_bookmarks_collection ON bookmarks(collection_id);
CREATE INDEX IF NOT EXISTS idx_bookmarks_favourite ON bookmarks(is_favourite);
CREATE INDEX IF NOT EXISTS idx_bookmark_tags_tag ON bookmark_tags(tag_name);
```

**`app/seed.py`** — `seed_demo_data(db_path: str)`:
- 3 collections: "Development" (#3b82f6), "Design" (#f59e0b), "Research" (#8b5cf6)
- 15 bookmarks with realistic URLs to real sites (GitHub, MDN, Stack Overflow, Dribbble, arXiv, etc.)
- 8-10 tags: python, javascript, api, design, ai, database, frontend, backend, devops, security
- Each bookmark has 1-3 tags
- 5 bookmarks in Development, 4 in Design, 3 in Research, 3 with no collection
- 4 bookmarks marked as favourite
- Idempotent with INSERT OR IGNORE

**`requirements.txt`**:
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
pytest>=7.4.0
httpx>=0.25.0
```

**`.env.example`**:
```
DATABASE_URL=sqlite:///data/bookmarks.db
API_HOST=0.0.0.0
API_PORT=8000
```

---

### Agent 2 — REST Endpoints and Main App

**`app/main.py`** — FastAPI application:
- Title: "Bookmark Manager API", version "1.0.0"
- Lifespan: init_db() on startup, seed if bookmarks table is empty
- Include all routers
- `GET /health` → `{"status": "ok", "version": "1.0.0"}`

**`app/routes/__init__.py`** — empty

**`app/routes/bookmarks.py`** — APIRouter prefix `/api/bookmarks`:

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/bookmarks` | Create bookmark with tags (create tags if they don't exist) |
| GET | `/api/bookmarks` | List bookmarks. Filters: `collection_id`, `tag`, `is_favourite` (bool), `limit` (default 50), `offset` |
| GET | `/api/bookmarks/{id}` | Get bookmark with tags |
| PUT | `/api/bookmarks/{id}` | Update bookmark fields and/or tags |
| DELETE | `/api/bookmarks/{id}` | Delete bookmark (cascade removes bookmark_tags) |
| POST | `/api/bookmarks/{id}/favourite` | Toggle favourite status |

Creating a bookmark:
1. INSERT into bookmarks
2. For each tag in tags list: INSERT OR IGNORE into tags, then INSERT into bookmark_tags
3. Return BookmarkResponse with tags populated

Updating tags:
1. DELETE FROM bookmark_tags WHERE bookmark_id = ?
2. Re-insert new tag associations
3. Clean up orphaned tags (tags with no bookmarks)

**`app/routes/collections.py`** — APIRouter prefix `/api/collections`:

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/collections` | Create collection |
| GET | `/api/collections` | List collections with bookmark_count |
| GET | `/api/collections/{id}` | Get collection with bookmark_count |
| PUT | `/api/collections/{id}` | Update collection |
| DELETE | `/api/collections/{id}` | Delete collection (bookmarks set collection_id=NULL) |

bookmark_count: `SELECT COUNT(*) FROM bookmarks WHERE collection_id = ?`

**`app/routes/tags.py`** — APIRouter prefix `/api/tags`:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/tags` | List all tags with bookmark_count |
| DELETE | `/api/tags/{name}` | Delete tag (removes from all bookmarks) |

---

### Agent 3 — Search, Import/Export, Tests, README

**`app/services/__init__.py`** — empty

**`app/services/search.py`** — Full-text search:
```python
def search_bookmarks(db, query: str, limit: int = 50, offset: int = 0) -> list[dict]:
    """Search bookmarks by title, URL, and description using LIKE."""
```
- Query: `SELECT * FROM bookmarks WHERE title LIKE ? OR url LIKE ? OR description LIKE ?`
- Pattern: `%{query}%` (case-insensitive via COLLATE NOCASE or LOWER())
- Return list of bookmark dicts with tags populated

Create a separate search router `app/routes/search.py` (do NOT modify agent 2's bookmarks.py — avoids merge conflicts):
- APIRouter prefix `/api/bookmarks`
- `GET /api/bookmarks/search?q=python&limit=20` — returns matching bookmarks
- Include this router in main.py by adding it alongside the other routers

**`app/services/import_export.py`** — Bookmark import/export:
```python
def export_bookmarks(db, collection_id: str | None = None) -> dict:
    """Export all bookmarks (or filtered by collection) as a dict."""

def import_bookmarks(db, data: dict) -> dict:
    """Import bookmarks from exported JSON. Returns {"imported": count, "skipped": count}."""
```

Create a separate import/export router `app/routes/import_export.py` (do NOT modify agent 2's bookmarks.py):
- APIRouter prefix `/api/bookmarks`
- `GET /api/bookmarks/export` — returns JSON with all bookmarks (optional `?collection_id=` filter)
- `POST /api/bookmarks/import` — accepts JSON body from export, creates bookmarks that don't exist (match by URL)
- Include this router in main.py by adding it alongside the other routers

**`tests/conftest.py`** — Test fixtures:
- `db_path` fixture: temporary SQLite file, cleaned up after tests
- `client` fixture: TestClient with fresh database and seed data

**`tests/test_api.py`** — 15+ integration tests:

Bookmark tests:
- `test_create_bookmark` — POST returns 201 with tags
- `test_create_bookmark_creates_tags` — new tags auto-created in tags table
- `test_list_bookmarks` — GET returns seeded bookmarks
- `test_list_bookmarks_filter_tag` — `?tag=python` returns only tagged bookmarks
- `test_list_bookmarks_filter_favourite` — `?is_favourite=true` returns only favourites
- `test_list_bookmarks_filter_collection` — `?collection_id=X` returns only that collection's bookmarks
- `test_get_bookmark` — GET by id returns bookmark with tags
- `test_update_bookmark_tags` — PUT with new tags replaces old tags
- `test_delete_bookmark` — DELETE returns 204, bookmark gone
- `test_toggle_favourite` — POST /favourite flips is_favourite

Collection tests:
- `test_create_collection` — POST returns 201
- `test_list_collections_with_count` — bookmark_count is correct
- `test_delete_collection_nulls_bookmarks` — bookmarks keep existing but collection_id becomes null

Search and import/export:
- `test_search_by_title` — finds bookmarks matching title
- `test_search_by_url` — finds bookmarks matching URL
- `test_export_import_roundtrip` — export all, delete all, import, verify count matches

General:
- `test_health_check` — GET /health returns 200
- `test_pagination` — limit and offset work correctly

**`README.md`** — Full documentation:
- Project description
- Quick start (3 commands: pip install, set DATABASE_URL, uvicorn)
- Full endpoint table with method, path, description
- Search usage examples
- Import/export usage examples
- Environment variables
- Running tests
- Project structure tree

## Verification Checklist

1. `python -c "from app.main import app; print('App OK')"` — imports without error
2. `pytest tests/ -v` — all 15+ tests pass
3. GET /health returns 200
4. POST /api/bookmarks creates bookmark with tags
5. GET /api/bookmarks/search?q=python returns matching results
6. GET /api/bookmarks/export returns all bookmarks as JSON
7. POST /api/bookmarks/import re-creates exported bookmarks
8. GET /api/collections returns collections with correct bookmark_count
9. DELETE bookmark cascades to bookmark_tags
10. DELETE collection sets bookmarks' collection_id to NULL
