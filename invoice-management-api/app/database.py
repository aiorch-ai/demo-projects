"""SQLite connection manager for the invoice management API."""

import os
import sqlite3
from pathlib import Path

from app.schema import SCHEMA


def init_db() -> None:
    """Initialize the database: create tables, indexes, and set pragmas.

    Reads DATABASE_URL from environment. Raises if not set or empty.
    """
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL environment variable is not set or empty")

    db_path = db_url.replace("sqlite:///", "", 1)

    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()

    os.chmod(db_path, 0o600)


def get_db():
    """Yield a SQLite connection configured for the invoice API.

    FastAPI Depends-compatible generator. Commits on success,
    rolls back on exception, always closes the connection.
    """
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL environment variable is not set or empty")

    db_path = db_url.replace("sqlite:///", "", 1)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
