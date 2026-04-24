from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from typing import Iterator


_SQLITE_URL_PREFIX = "sqlite:///"


def _db_path_from_url(url: str) -> str:
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
            "Set it to a sqlite URL like 'sqlite:///data/contacts.db'."
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
CREATE TABLE IF NOT EXISTS contacts (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    company TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_contacts_name ON contacts(name);
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
