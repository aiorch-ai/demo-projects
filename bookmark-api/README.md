# Bookmark Manager API

A small FastAPI service for managing bookmarks, collections, and tags, backed
by SQLite. Supports CRUD on bookmarks/collections, listing/deleting tags,
case-insensitive search, and JSON import/export.

## Quick Start

```bash
pip install -r requirements.txt
export DATABASE_URL=sqlite:///data/bookmarks.db
uvicorn app.main:app --reload
```

The application creates the SQLite file (and parent directory) on first startup
and seeds 15 demo bookmarks if the `bookmarks` table is empty.

## Endpoints

| Method | Path                                  | Description                                      |
|--------|---------------------------------------|--------------------------------------------------|
| GET    | `/health`                             | Liveness probe — returns `{status, version}`     |
| POST   | `/api/bookmarks`                      | Create a bookmark                                |
| GET    | `/api/bookmarks`                      | List bookmarks (filters: `collection_id`, `tag`, `is_favourite`; `limit`, `offset`) |
| GET    | `/api/bookmarks/{id}`                 | Fetch a single bookmark                          |
| PUT    | `/api/bookmarks/{id}`                 | Update a bookmark (partial; `tags` replaces all) |
| DELETE | `/api/bookmarks/{id}`                 | Delete a bookmark                                |
| POST   | `/api/bookmarks/{id}/favourite`       | Toggle the `is_favourite` flag                   |
| GET    | `/api/bookmarks/search`               | Search by title/url/description (`q`, `limit`, `offset`) |
| GET    | `/api/bookmarks/export`               | Export bookmarks (optional `collection_id`)      |
| POST   | `/api/bookmarks/import`               | Import an export-shaped JSON payload             |
| POST   | `/api/collections`                    | Create a collection                              |
| GET    | `/api/collections`                    | List collections with bookmark counts            |
| GET    | `/api/collections/{id}`               | Fetch a collection                               |
| PUT    | `/api/collections/{id}`               | Update a collection                              |
| DELETE | `/api/collections/{id}`               | Delete a collection (bookmarks set to `null`)    |
| GET    | `/api/tags`                           | List tags with bookmark counts                   |
| DELETE | `/api/tags/{name}`                    | Delete a tag (cascades to `bookmark_tags`)       |

## Search

The search endpoint runs a single parameterized SQL query against `title`,
`url`, and `description` using `LIKE ... COLLATE NOCASE`.

```bash
curl 'http://localhost:8000/api/bookmarks/search?q=python'
curl 'http://localhost:8000/api/bookmarks/search?q=fastapi&limit=10&offset=0'
```

## Import / Export

Export every bookmark as JSON (or filter by collection):

```bash
curl 'http://localhost:8000/api/bookmarks/export' > backup.json
curl 'http://localhost:8000/api/bookmarks/export?collection_id=col-development' > dev.json
```

Re-import the same payload. URLs already present are skipped:

```bash
curl -X POST 'http://localhost:8000/api/bookmarks/import' \
     -H 'Content-Type: application/json' \
     --data @backup.json
# -> {"imported": 0, "skipped": 15}
```

The export shape is `{bookmarks: [...], exported_at: "...", count: N}` where
each bookmark mirrors the `BookmarkResponse` model (including its `tags`).

## Environment Variables

| Variable        | Required | Default                       | Notes                           |
|-----------------|----------|-------------------------------|---------------------------------|
| `DATABASE_URL`  | yes      | (none — fails if unset)       | `sqlite:///path/to/file.db`     |
| `API_HOST`      | no       | `0.0.0.0`                     | For uvicorn binding             |
| `API_PORT`      | no       | `8000`                        | For uvicorn binding             |

A starter `.env.example` is checked in.

## Running Tests

From the `bookmark-api/` directory:

```bash
pytest tests/ -v
```

Tests are function-scoped — each test gets a fresh, seeded SQLite file via the
`client` fixture in `tests/conftest.py`.

## Project Structure

```
bookmark-api/
├── app/
│   ├── __init__.py
│   ├── database.py            # SQLite connection + schema (init_db, get_db)
│   ├── main.py                # FastAPI app, lifespan (init + seed-if-empty)
│   ├── models.py              # Pydantic v2 models
│   ├── seed.py                # Idempotent demo data
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── bookmarks.py       # /api/bookmarks CRUD + favourite toggle
│   │   ├── collections.py     # /api/collections CRUD
│   │   ├── tags.py            # /api/tags list + delete
│   │   ├── search.py          # /api/bookmarks/search
│   │   └── import_export.py   # /api/bookmarks/{export,import}
│   └── services/
│       ├── __init__.py
│       ├── search.py          # parameterized LIKE search
│       └── import_export.py   # export/import logic
├── tests/
│   ├── conftest.py            # db_path + client fixtures
│   ├── test_api.py            # integration tests for all endpoints
│   ├── test_db_seed.py        # database init + seed tests
│   └── test_routes_smoke.py   # smoke tests for the route layer
├── .env.example
├── pytest.ini
├── requirements.txt
└── README.md
```
