"""SQLite connection manager for the Weather Dashboard API.

DATABASE_URL is read lazily from os.environ inside init_db() and get_db()
so that importing this module does not require the env var to be set.
"""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from typing import Iterator


_SQLITE_URL_PREFIX = "sqlite:///"


def _db_path_from_url(url: str) -> str:
    """Strip the `sqlite:///` prefix to yield a filesystem path and ensure parent dir exists."""
    if not url.startswith(_SQLITE_URL_PREFIX):
        raise RuntimeError(
            f"DATABASE_URL must start with '{_SQLITE_URL_PREFIX}'; got: {url!r}"
        )
    path = url[len(_SQLITE_URL_PREFIX):]
    if not path:
        raise RuntimeError("DATABASE_URL is missing a filesystem path after 'sqlite:///'")
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    return path


def _require_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL environment variable is not set. "
            "Set it to a sqlite URL like 'sqlite:///data/weather.db'."
        )
    return url


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db() -> Iterator[sqlite3.Connection]:
    """Context manager yielding a sqlite3.Connection configured for this app.

    Commits on successful exit; rolls back on exception; always closes.
    """
    url = _require_database_url()
    db_path = _db_path_from_url(url)
    conn = _connect(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


SCHEMA = """
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
"""


def init_db() -> None:
    """Create all tables and indexes. Idempotent."""
    url = _require_database_url()
    db_path = _db_path_from_url(url)
    conn = _connect(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()
