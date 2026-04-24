from __future__ import annotations

import sqlite3

import pytest


def test_require_database_url_unset(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    import sys

    for mod_name in list(sys.modules):
        if mod_name == "contacts" or mod_name.startswith("contacts."):
            del sys.modules[mod_name]

    from contacts.db import _require_database_url

    with pytest.raises(RuntimeError, match="DATABASE_URL environment variable is not set"):
        _require_database_url()


def test_db_path_from_url_bad_prefix():
    import sys

    for mod_name in list(sys.modules):
        if mod_name == "contacts" or mod_name.startswith("contacts."):
            del sys.modules[mod_name]

    from contacts.db import _db_path_from_url

    with pytest.raises(RuntimeError, match="must start with 'sqlite:///'"):
        _db_path_from_url("postgres://localhost/db")


def test_db_path_from_url_missing_path():
    import sys

    for mod_name in list(sys.modules):
        if mod_name == "contacts" or mod_name.startswith("contacts."):
            del sys.modules[mod_name]

    from contacts.db import _db_path_from_url

    with pytest.raises(RuntimeError, match="missing a filesystem path"):
        _db_path_from_url("sqlite:///")


def test_init_db_creates_tables_and_index(fresh_db):
    from contacts.db import get_db

    with get_db() as conn:
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='contacts'"
        )
        assert cur.fetchone() is not None

        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_contacts_name'"
        )
        assert cur.fetchone() is not None


def test_init_db_is_idempotent(fresh_db):
    from contacts.db import init_db

    init_db()
    init_db()


def test_get_db_commits_on_success(fresh_db):
    from contacts.db import get_db

    with get_db() as conn:
        conn.execute(
            "INSERT INTO contacts (id, name) VALUES (?, ?)",
            ("abc", "Alice"),
        )

    with get_db() as conn:
        cur = conn.execute("SELECT name FROM contacts WHERE id = ?", ("abc",))
        row = cur.fetchone()
        assert row is not None
        assert row["name"] == "Alice"


def test_get_db_rolls_back_on_exception(fresh_db):
    from contacts.db import get_db

    with pytest.raises(ValueError):
        with get_db() as conn:
            conn.execute(
                "INSERT INTO contacts (id, name) VALUES (?, ?)",
                ("def", "Bob"),
            )
            raise ValueError("boom")

    with get_db() as conn:
        cur = conn.execute("SELECT id FROM contacts WHERE id = ?", ("def",))
        assert cur.fetchone() is None


def test_get_db_row_factory(fresh_db):
    from contacts.db import get_db

    with get_db() as conn:
        conn.execute(
            "INSERT INTO contacts (id, name, email) VALUES (?, ?, ?)",
            ("ghi", "Carol", "carol@example.com"),
        )

    with get_db() as conn:
        cur = conn.execute("SELECT * FROM contacts WHERE id = ?", ("ghi",))
        row = cur.fetchone()
        assert isinstance(row, sqlite3.Row)
        assert row["name"] == "Carol"
        assert row["email"] == "carol@example.com"
