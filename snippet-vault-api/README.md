# Snippet Vault API

Snippet Vault API is a small FastAPI service backed by SQLite for storing code snippets, tags, and lightweight usage stats.

## Quick Start

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

3. Set environment variables:

```bash
cp .env.example .env
export DATABASE_URL=sqlite:///data/snippets.db
export API_HOST=0.0.0.0
export API_PORT=8002
```

4. Start the API from the project directory:

```bash
uvicorn app.main:app --host "${API_HOST:-0.0.0.0}" --port "${API_PORT:-8002}" --reload
```

On startup the app initializes the SQLite schema and seeds 10 demo snippets only when the `snippets` table is empty.

## Environment Variables

| Variable | Required | Description |
| --- | --- | --- |
| `DATABASE_URL` | Yes | SQLite database URL. Must use the `sqlite:///path/to/file.db` format. |
| `API_HOST` | No | Host passed to `uvicorn`. `.env.example` uses `0.0.0.0`. |
| `API_PORT` | No | Port passed to `uvicorn`. `.env.example` uses `8002`. |

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Health check returning API status and version. |
| `POST` | `/api/snippets` | Create a snippet and create any missing tags. |
| `GET` | `/api/snippets` | List snippets with optional `language`, `tag`, `is_public`, `limit`, and `offset` filters. |
| `GET` | `/api/snippets/search` | Search snippet `title`, `description`, and `code` with required `q`, plus optional `language`, `limit`, and `offset`. |
| `GET` | `/api/snippets/{snippet_id}` | Fetch one snippet and increment its `view_count`. |
| `PUT` | `/api/snippets/{snippet_id}` | Update snippet fields and optionally replace all tags. |
| `DELETE` | `/api/snippets/{snippet_id}` | Delete a snippet and its tag links. |
| `GET` | `/api/tags` | List tags with snippet usage counts. |
| `DELETE` | `/api/tags/{name}` | Delete a tag globally and remove it from all snippets. |
| `GET` | `/api/stats/languages` | Return snippet counts grouped by language. |
| `GET` | `/api/stats/popular` | Return the top 5 snippets ordered by popularity. |

## Test Instructions

Run the verification commands from the project directory:

```bash
python3 -c "from app.main import app; print('App OK')"
python3 -m pytest tests/ -v
```

The test suite covers database initialization, seed idempotency, CRUD flows, search, stats, and startup seeding behavior.
