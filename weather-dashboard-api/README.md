# Weather Dashboard API

A lightweight FastAPI service for tracking city weather data, favourites, and historical lookups backed by SQLite.

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Copy the example environment file and edit as needed:
   ```bash
   cp .env.example .env
   ```

3. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8001` by default.

## Endpoints

### Cities

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/cities` | Create a new city |
| GET | `/api/cities` | List cities (optional filters: `country`, `is_favourite`) |
| GET | `/api/cities/{id}` | Get a single city by ID |
| DELETE | `/api/cities/{id}` | Delete a city (cascades to weather records) |
| POST | `/api/cities/{id}/favourite` | Toggle favourite status for a city |
| GET | `/api/cities/{id}/summary` | Get city summary with latest weather and record count |

### Weather Records

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/weather` | Record a new weather observation |
| GET | `/api/weather/{city_id}` | Get weather history for a city (ordered by `recorded_at` DESC) |
| GET | `/api/weather/{city_id}/latest` | Get the latest weather record for a city |
| DELETE | `/api/weather/{record_id}` | Delete a weather record |

### Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check — returns `{"status": "ok", "version": "1.0.0"}` |

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | SQLite database URL (required) | `sqlite:///data/weather.db` |
| `API_HOST` | Host to bind the server | `0.0.0.0` |
| `API_PORT` | Port to bind the server | `8001` |

## Running Tests

```bash
pytest tests/ -v
```

Tests use a temporary SQLite database per test case and include seeded demo data (5 cities, 30 weather records).
