# Orchestrator Prompt — Weather Dashboard API

Read the task file: `/opt/orchestrator/v3/sample_tasks/demo-projects/weather-dashboard-api/task.md`

## Delivery Principals

- No hardcoding — all configuration from environment variables
- No fallbacks — fail explicitly if DATABASE_URL is not set
- No mock data — seed data must be realistic weather readings
- All Pydantic models must use v2 syntax
- Use uuid4 for all primary keys (stored as TEXT in SQLite)
- Seed data must be idempotent (INSERT OR IGNORE)
- All tests must pass: `pytest tests/ -v`

## Pre-Existing Infrastructure

Greenfield project. The git repo at `/opt/orchestrator/v3/sample_tasks/demo-projects/` has only sample task files on the `main` branch.

## What to Build

### Agent 1 — Database, Models, Seed Data

**`weather-dashboard-api/app/__init__.py`** — empty

**`weather-dashboard-api/app/database.py`** — SQLite connection manager:
- Read `DATABASE_URL` from `os.environ` — no default, raise RuntimeError if missing
- WAL mode, busy_timeout=5000, foreign_keys=ON
- `init_db()` creates tables, `get_db()` yields connection with row_factory=sqlite3.Row

**`weather-dashboard-api/app/models.py`** — Pydantic v2 models:
- `CityCreate(name: str, country: str, latitude: float, longitude: float)`
- `CityResponse(id, name, country, latitude, longitude, is_favourite: bool, created_at)`
- `WeatherRecordCreate(city_id: str, temperature_c: float, humidity: int, wind_speed_kmh: float, condition: str, recorded_at: str | None)`
- `WeatherRecordResponse(id, city_id, temperature_c, humidity, wind_speed_kmh, condition, recorded_at)`
- `CityWeatherSummary(city: CityResponse, latest: WeatherRecordResponse | None, record_count: int)`

**Database schema** (2 tables):
```sql
CREATE TABLE IF NOT EXISTS cities (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    country TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    is_favourite INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(name, country)
);

CREATE TABLE IF NOT EXISTS weather_records (
    id TEXT PRIMARY KEY,
    city_id TEXT NOT NULL REFERENCES cities(id) ON DELETE CASCADE,
    temperature_c REAL NOT NULL,
    humidity INTEGER NOT NULL,
    wind_speed_kmh REAL NOT NULL,
    condition TEXT NOT NULL,
    recorded_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_weather_city ON weather_records(city_id);
CREATE INDEX IF NOT EXISTS idx_weather_recorded ON weather_records(recorded_at);
```

**`weather-dashboard-api/app/seed.py`** — `seed_demo_data(db_path: str)`:
- 5 cities: London/UK, Tokyo/JP, New York/US, Sydney/AU, Berlin/DE with real coordinates
- 30 weather records spread across the 5 cities (6 each), realistic temps per city
- Conditions: sunny, cloudy, rainy, partly_cloudy, stormy, snowy
- 2 cities marked as favourite (Tokyo, Sydney)
- Idempotent with INSERT OR IGNORE

**`weather-dashboard-api/requirements.txt`**:
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
pytest>=7.4.0
httpx>=0.25.0
```

**`weather-dashboard-api/.env.example`**:
```
DATABASE_URL=sqlite:///data/weather.db
API_HOST=0.0.0.0
API_PORT=8001
```

---

### Agent 2 — REST Endpoints, Tests, README

**`weather-dashboard-api/app/main.py`** — FastAPI application:
- Title: "Weather Dashboard API", version "1.0.0"
- Lifespan: init_db() on startup, seed if cities table is empty
- Include all routers
- `GET /health` → `{"status": "ok", "version": "1.0.0"}`

**`weather-dashboard-api/app/routes/__init__.py`** — empty

**`weather-dashboard-api/app/routes/cities.py`** — APIRouter prefix `/api/cities`:

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/cities` | Create city |
| GET | `/api/cities` | List cities. Filters: `country`, `is_favourite` (bool) |
| GET | `/api/cities/{id}` | Get city |
| DELETE | `/api/cities/{id}` | Delete city (cascade deletes weather records) |
| POST | `/api/cities/{id}/favourite` | Toggle favourite status |
| GET | `/api/cities/{id}/summary` | Get city with latest weather and record count |

**`weather-dashboard-api/app/routes/weather.py`** — APIRouter prefix `/api/weather`:

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/weather` | Record weather observation for a city |
| GET | `/api/weather/{city_id}` | Get weather history for a city. Params: `limit` (default 10), `offset` |
| GET | `/api/weather/{city_id}/latest` | Get latest weather record for a city |
| DELETE | `/api/weather/{record_id}` | Delete a weather record |

**`weather-dashboard-api/tests/conftest.py`** — Test fixtures:
- `db_path` fixture: temporary SQLite file, cleaned up after tests
- `client` fixture: TestClient with fresh database and seed data

**`weather-dashboard-api/tests/test_api.py`** — 12+ integration tests:
- `test_health_check` — GET /health returns 200
- `test_create_city` — POST returns 201
- `test_list_cities` — GET returns seeded cities
- `test_list_cities_filter_country` — `?country=JP` returns only Japanese cities
- `test_list_cities_filter_favourite` — `?is_favourite=true` returns favourites
- `test_delete_city_cascades` — DELETE city also deletes its weather records
- `test_toggle_favourite` — POST /favourite flips is_favourite
- `test_city_summary` — GET /summary returns latest weather and count
- `test_record_weather` — POST creates weather record
- `test_weather_history` — GET returns records ordered by recorded_at desc
- `test_weather_latest` — GET /latest returns most recent record
- `test_weather_pagination` — limit and offset work

**`weather-dashboard-api/README.md`** — Project documentation:
- Quick start, endpoint table, environment variables, running tests

## Verification Checklist

1. `python -c "from app.main import app; print('App OK')"` — imports without error (run from weather-dashboard-api/)
2. `pytest tests/ -v` — all 12+ tests pass
3. GET /health returns 200
4. POST /api/cities creates city
5. POST /api/weather records observation
6. GET /api/cities/{id}/summary returns latest weather
