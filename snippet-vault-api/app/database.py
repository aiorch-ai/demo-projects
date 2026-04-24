"""SQLite connection manager for the Snippet Vault API."""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from typing import Iterator


_SQLITE_URL_PREFIX = "sqlite:///"


def _require_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL environment variable is not set. "
            "Set it to a sqlite URL like 'sqlite:///data/snippets.db'."
        )
    return url


def _db_path_from_url(url: str) -> str:
    if not url.startswith(_SQLITE_URL_PREFIX):
        raise RuntimeError(
            f"DATABASE_URL must start with '{_SQLITE_URL_PREFIX}'; got: {url!r}"
        )

    db_path = url[len(_SQLITE_URL_PREFIX) :]
    if not db_path:
        raise RuntimeError("DATABASE_URL is missing a filesystem path after 'sqlite:///'")

    parent = os.path.dirname(db_path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    return db_path


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db() -> Iterator[sqlite3.Connection]:
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
"""


def init_db() -> None:
    url = _require_database_url()
    db_path = _db_path_from_url(url)
    conn = _connect(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()
