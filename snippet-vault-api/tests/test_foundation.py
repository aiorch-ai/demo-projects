from __future__ import annotations

import sqlite3

import pytest


def test_init_db_requires_database_url(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    from app.database import init_db

    with pytest.raises(RuntimeError, match="DATABASE_URL environment variable is not set"):
        init_db()


def test_init_db_creates_schema_and_indexes(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "snippets.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    from app.database import get_db, init_db

    init_db()

    with get_db() as conn:
        tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        }
        indexes = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        }
        foreign_keys = conn.execute("PRAGMA foreign_keys").fetchone()[0]
        busy_timeout = conn.execute("PRAGMA busy_timeout").fetchone()[0]
        journal_mode = conn.execute("PRAGMA journal_mode").fetchone()[0]

    assert tables == {"snippets", "snippet_tags", "tags"}
    assert indexes == {
        "idx_snippet_tags_tag",
        "idx_snippets_language",
        "idx_snippets_public",
    }
    assert foreign_keys == 1
    assert busy_timeout == 5000
    assert journal_mode.lower() == "wal"


def test_seed_demo_data_is_idempotent_and_matches_expected_content(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "snippets.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    from app.database import init_db
    from app.seed import seed_demo_data

    init_db()
    seed_demo_data(str(db_path))
    seed_demo_data(str(db_path))

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        snippet_count = conn.execute("SELECT COUNT(*) FROM snippets").fetchone()[0]
        tag_count = conn.execute("SELECT COUNT(*) FROM tags").fetchone()[0]
        snippet_tag_count = conn.execute("SELECT COUNT(*) FROM snippet_tags").fetchone()[0]
        private_count = conn.execute(
            "SELECT COUNT(*) FROM snippets WHERE is_public = 0"
        ).fetchone()[0]
        languages = {
            row["language"]: row["snippet_count"]
            for row in conn.execute(
                """
                SELECT language, COUNT(*) AS snippet_count
                FROM snippets
                GROUP BY language
                ORDER BY language
                """
            ).fetchall()
        }
        tagged_rows = conn.execute(
            """
            SELECT s.title, COUNT(st.tag_name) AS tag_count
            FROM snippets AS s
            LEFT JOIN snippet_tags AS st ON st.snippet_id = s.id
            GROUP BY s.id
            ORDER BY s.title
            """
        ).fetchall()
    finally:
        conn.close()

    assert snippet_count == 10
    assert tag_count == 8
    assert snippet_tag_count == 21
    assert private_count == 3
    assert languages == {
        "bash": 2,
        "go": 2,
        "javascript": 2,
        "python": 2,
        "sql": 2,
    }
    assert all(1 <= row["tag_count"] <= 3 for row in tagged_rows)
