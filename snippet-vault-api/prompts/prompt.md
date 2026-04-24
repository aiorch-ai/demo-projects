# Orchestrator Prompt — Snippet Vault API

Read the task file: `/opt/orchestrator/v3/sample_tasks/demo-projects/snippet-vault-api/task.md`

## Delivery Principals

- No hardcoding — all configuration from environment variables
- No fallbacks — fail explicitly if DATABASE_URL is not set
- No mock data — seed data must be realistic code snippets
- All Pydantic models must use v2 syntax
- Use uuid4 for all primary keys (stored as TEXT in SQLite)
- Seed data must be idempotent (INSERT OR IGNORE)
- All tests must pass: `pytest tests/ -v`

## Pre-Existing Infrastructure

Greenfield project. The git repo at `/opt/orchestrator/v3/sample_tasks/demo-projects/` has only sample task files on the `main` branch.

## What to Build

### Agent 1 — Database, Models, Seed Data

**`snippet-vault-api/app/__init__.py`** — empty

**`snippet-vault-api/app/database.py`** — SQLite connection manager:
- Read `DATABASE_URL` from `os.environ` — no default, raise RuntimeError if missing
- WAL mode, busy_timeout=5000, foreign_keys=ON
- `init_db()` creates tables, `get_db()` yields connection with row_factory=sqlite3.Row

**`snippet-vault-api/app/models.py`** — Pydantic v2 models:
- `SnippetCreate(title: str, code: str, language: str, description: str | None, tags: list[str] = [], is_public: bool = True)`
- `SnippetResponse(id, title, code, language, description, tags: list[str], is_public: bool, view_count: int, created_at, updated_at)`
- `SnippetUpdate(title: str | None, code: str | None, language: str | None, description: str | None, is_public: bool | None, tags: list[str] | None)`
- `TagResponse(name: str, snippet_count: int)`
- `LanguageStats(language: str, snippet_count: int)`

**Database schema** (3 tables):
```sql
CREATE TABLE IF NOT EXISTS snippets (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    code TEXT NOT NULL,
    language TEXT NOT NULL,
    description TEXT,
    is_public INTEGER NOT NULL DEFAULT 1,
    view_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tags (
    name TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS snippet_tags (
    snippet_id TEXT NOT NULL REFERENCES snippets(id) ON DELETE CASCADE,
    tag_name TEXT NOT NULL REFERENCES tags(name) ON DELETE CASCADE,
    PRIMARY KEY (snippet_id, tag_name)
);

CREATE INDEX IF NOT EXISTS idx_snippets_language ON snippets(language);
CREATE INDEX IF NOT EXISTS idx_snippets_public ON snippets(is_public);
CREATE INDEX IF NOT EXISTS idx_snippet_tags_tag ON snippet_tags(tag_name);
```

**`snippet-vault-api/app/seed.py`** — `seed_demo_data(db_path: str)`:
- 10 snippets across 5 languages: python, javascript, go, sql, bash
- Realistic code content (e.g., Python: fibonacci function, JS: fetch wrapper, Go: HTTP handler, SQL: window function, Bash: log rotation script)
- 8 tags: algorithm, web, api, database, devops, utility, beginner, advanced
- Each snippet has 1-3 tags
- 3 snippets marked as private (is_public=False)
- Idempotent with INSERT OR IGNORE

**`snippet-vault-api/requirements.txt`**:
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
pytest>=7.4.0
httpx>=0.25.0
```

**`snippet-vault-api/.env.example`**:
```
DATABASE_URL=sqlite:///data/snippets.db
API_HOST=0.0.0.0
API_PORT=8002
```

---

### Agent 2 — REST Endpoints, Search, Tests, README

**`snippet-vault-api/app/main.py`** — FastAPI application:
- Title: "Snippet Vault API", version "1.0.0"
- Lifespan: init_db() on startup, seed if snippets table is empty
- Include all routers
- `GET /health` → `{"status": "ok", "version": "1.0.0"}`

**`snippet-vault-api/app/routes/__init__.py`** — empty

**`snippet-vault-api/app/routes/snippets.py`** — APIRouter prefix `/api/snippets`:

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/snippets` | Create snippet with tags (create tags if they don't exist) |
| GET | `/api/snippets` | List snippets. Filters: `language`, `tag`, `is_public` (bool), `limit` (default 20), `offset` |
| GET | `/api/snippets/{id}` | Get snippet (increments view_count) |
| PUT | `/api/snippets/{id}` | Update snippet fields and/or tags |
| DELETE | `/api/snippets/{id}` | Delete snippet (cascade removes snippet_tags) |
| GET | `/api/snippets/search` | Search by title, description, code using LIKE. Params: `q`, `language`, `limit`, `offset` |

**`snippet-vault-api/app/routes/tags.py`** — APIRouter prefix `/api/tags`:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/tags` | List all tags with snippet_count |
| DELETE | `/api/tags/{name}` | Delete tag (removes from all snippets) |

**`snippet-vault-api/app/routes/stats.py`** — APIRouter prefix `/api/stats`:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/stats/languages` | List languages with snippet counts |
| GET | `/api/stats/popular` | Top 5 snippets by view_count |

**`snippet-vault-api/tests/conftest.py`** — Test fixtures:
- `db_path` fixture: temporary SQLite file, cleaned up after tests
- `client` fixture: TestClient with fresh database and seed data

**`snippet-vault-api/tests/test_api.py`** — 14+ integration tests:
- `test_health_check` — GET /health returns 200
- `test_create_snippet` — POST returns 201 with tags
- `test_create_snippet_creates_tags` — new tags auto-created
- `test_list_snippets` — GET returns seeded snippets
- `test_list_snippets_filter_language` — `?language=python` returns only Python snippets
- `test_list_snippets_filter_tag` — `?tag=api` returns tagged snippets
- `test_list_snippets_filter_public` — `?is_public=false` returns private only
- `test_get_snippet_increments_views` — GET by id bumps view_count
- `test_update_snippet_tags` — PUT with new tags replaces old tags
- `test_delete_snippet` — DELETE returns 204
- `test_search_by_title` — finds snippets matching title
- `test_search_by_code` — finds snippets matching code content
- `test_language_stats` — returns correct counts per language
- `test_popular_snippets` — returns top 5 by view_count

**`snippet-vault-api/README.md`** — Project documentation:
- Quick start, endpoint table, environment variables, running tests

## Verification Checklist

1. `python -c "from app.main import app; print('App OK')"` — imports without error (run from snippet-vault-api/)
2. `pytest tests/ -v` — all 14+ tests pass
3. GET /health returns 200
4. POST /api/snippets creates snippet with tags
5. GET /api/snippets/search?q=fibonacci returns matching results
6. GET /api/stats/languages returns language breakdown
7. GET /api/snippets/{id} increments view_count
