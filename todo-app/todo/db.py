"""SQLite connection manager for the Todo CLI.

TODO_DB_PATH is read lazily from os.environ inside init_db() and get_db()
so that importing this module does not require the env var to be set.
"""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from typing import Iterator


def _require_db_path() -> str:
    """Return the database path from TODO_DB_PATH, defaulting to ~/.todo/todos.db."""
    path = os.environ.get("TODO_DB_PATH")
    if not path:
        path = os.path.expanduser("~/.todo/todos.db")
    return path


def _ensure_parent_dir(db_path: str) -> str:
    """Ensure the parent directory for db_path exists."""
    parent = os.path.dirname(db_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    return db_path


def _connect(db_path: str) -> sqlite3.Connection:
    """Open a sqlite3.Connection with app-specific settings."""
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
    db_path = _ensure_parent_dir(_require_db_path())
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
CREATE TABLE IF NOT EXISTS todos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    priority TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    due_date TEXT
);

CREATE INDEX IF NOT EXISTS idx_todos_status ON todos(status);
CREATE INDEX IF NOT EXISTS idx_todos_priority ON todos(priority);
CREATE INDEX IF NOT EXISTS idx_todos_due_date ON todos(due_date);
"""


def init_db() -> None:
    """Create all tables and indexes. Idempotent."""
    db_path = _ensure_parent_dir(_require_db_path())
    conn = _connect(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()
