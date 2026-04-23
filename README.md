# Bookmark Manager API

A FastAPI-based bookmark manager backed by SQLite. Organize URLs into
collections, tag them, mark favourites, and search across titles, URLs, and
descriptions. Ships with demo seed data, import/export, and a full test suite.

## Features

- Bookmarks with collections, tags, favourite flag
- Many-to-many tag relationship (tags auto-created on bookmark insert)
- LIKE-based case-insensitive search across title, URL, description
- JSON export / import (matches existing bookmarks by URL)
- Idempotent demo data seeding on first boot
- SQLite with WAL mode, `foreign_keys=ON`, `busy_timeout=5000`

## Quick Start

```bash
pip install -r requirements.txt
export DATABASE_URL=sqlite:///data/bookmarks.db
uvicorn app.main:app --reload
```

The API is then available at `http://localhost:8000`. Interactive docs are
served at `http://localhost:8000/docs`.

On first start, the database is created and seeded with 3 collections, 15
bookmarks, and 9 tags if the `bookmarks` table is empty.

## Endpoints

### Health

| Method | Path      | Description                         |
|--------|-----------|-------------------------------------|
| GET    | `/health` | Liveness probe — returns status/ver |

### Bookmarks (`/api/bookmarks`)

| Method | Path                               | Description                                                                 |
|--------|------------------------------------|-----------------------------------------------------------------------------|
| POST   | `/api/bookmarks`                   | Create a bookmark (tags auto-created)                                       |
| GET    | `/api/bookmarks`                   | List bookmarks. Filters: `collection_id`, `tag`, `is_favourite`, `limit`, `offset` |
| GET    | `/api/bookmarks/{id}`              | Fetch a single bookmark with its tags                                       |
| PUT    | `/api/bookmarks/{id}`              | Update fields and/or replace tags                                           |
| DELETE | `/api/bookmarks/{id}`              | Delete bookmark (cascades to `bookmark_tags`)                               |
| POST   | `/api/bookmarks/{id}/favourite`    | Toggle the favourite flag                                                   |

### Collections (`/api/collections`)

| Method | Path                         | Description                                               |
|--------|------------------------------|-----------------------------------------------------------|
| POST   | `/api/collections`           | Create a collection                                       |
| GET    | `/api/collections`           | List collections with `bookmark_count`                    |
| GET    | `/api/collections/{id}`      | Fetch one collection with `bookmark_count`                |
| PUT    | `/api/collections/{id}`      | Update a collection                                       |
| DELETE | `/api/collections/{id}`      | Delete collection — bookmarks keep existing, FK set NULL  |

### Tags (`/api/tags`)

| Method | Path                  | Description                                    |
|--------|-----------------------|------------------------------------------------|
| GET    | `/api/tags`           | List all tags with `bookmark_count`            |
| DELETE | `/api/tags/{name}`    | Delete tag (cascades to `bookmark_tags` rows)  |

### Search (`/api/bookmarks`)

| Method | Path                       | Description                                                |
|--------|----------------------------|------------------------------------------------------------|
| GET    | `/api/bookmarks/search`    | Query params: `q` (required), `limit`, `offset`            |

### Import / Export (`/api/bookmarks`)

| Method | Path                       | Description                                                     |
|--------|----------------------------|-----------------------------------------------------------------|
| GET    | `/api/bookmarks/export`    | Export all bookmarks (optional `?collection_id=` filter)        |
| POST   | `/api/bookmarks/import`    | Import from exported JSON; skips URLs already present          |

## Usage Examples

### Search

```bash
curl "http://localhost:8000/api/bookmarks/search?q=python&limit=10"
```

Returns a list of bookmark dicts whose title, URL, or description matches
`python` case-insensitively.

### Export

```bash
curl "http://localhost:8000/api/bookmarks/export" > bookmarks.json
```

Shape:

```json
{
  "bookmarks": [ { "id": "...", "url": "...", "title": "...", "tags": ["..."], ... } ],
  "exported_at": "2026-04-23T20:15:00.000000",
  "count": 15
}
```

Filter by collection:

```bash
curl "http://localhost:8000/api/bookmarks/export?collection_id=<collection-id>"
```

### Import

```bash
curl -X POST "http://localhost:8000/api/bookmarks/import" \
     -H "Content-Type: application/json" \
     -d @bookmarks.json
```

Response: `{"imported": <n>, "skipped": <m>}`. Existing URLs are skipped.

## Environment Variables

| Variable       | Required | Default              | Purpose                                 |
|----------------|----------|----------------------|-----------------------------------------|
| `DATABASE_URL` | Yes      | — (raises if unset)  | SQLite URL, e.g. `sqlite:///data/bookmarks.db` |
| `API_HOST`     | No       | `0.0.0.0`            | Host for uvicorn (see `.env.example`)   |
| `API_PORT`     | No       | `8000`               | Port for uvicorn                        |

`DATABASE_URL` must use the `sqlite:///` prefix. A relative path like
`sqlite:///data/bookmarks.db` is resolved against the current working
directory; the parent directory is created automatically on first run.

## Running Tests

```bash
pytest tests/ -v
```

Every test runs against an isolated tmp SQLite file seeded from scratch.
Tests exercise the full HTTP stack via FastAPI's `TestClient`.

## Project Structure

```
.
├── app
│   ├── __init__.py
│   ├── database.py            # connection manager, schema, init_db()
│   ├── models.py              # Pydantic v2 models
│   ├── seed.py                # idempotent demo data seeder
│   ├── main.py                # FastAPI app, lifespan, router wiring
│   ├── routes
│   │   ├── __init__.py
│   │   ├── bookmarks.py       # CRUD for bookmarks + /favourite
│   │   ├── collections.py     # CRUD for collections
│   │   ├── tags.py            # list/delete tags
│   │   ├── search.py          # GET /api/bookmarks/search
│   │   └── import_export.py   # GET /export, POST /import
│   └── services
│       ├── __init__.py
│       ├── search.py          # search_bookmarks()
│       └── import_export.py   # export_bookmarks() / import_bookmarks()
├── tests
│   ├── __init__.py
│   ├── conftest.py            # db_path + client fixtures
│   └── test_api.py            # 18 integration tests
├── requirements.txt
├── .env.example
└── README.md
```
