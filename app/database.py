"""SQLite connection manager for the Bookmark Manager API.

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
            "Set it to a sqlite URL like 'sqlite:///data/bookmarks.db'."
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
