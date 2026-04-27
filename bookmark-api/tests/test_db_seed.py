"""Smoke tests for database initialization and seed data."""

import os
import sqlite3

import pytest

from app.database import init_db
from app.seed import seed_demo_data


@pytest.fixture()
def tmp_db(tmp_path):
    """Set DATABASE_URL to a temporary database path and clean up after."""
    db_file = tmp_path / "test.db"
    old = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = f"sqlite:///{db_file}"
    yield db_file
    if old is None:
        os.environ.pop("DATABASE_URL", None)
    else:
        os.environ["DATABASE_URL"] = old


class TestInitDb:
    def test_creates_all_four_tables(self, tmp_db):
        """init_db() creates all 4 tables: collections, bookmarks, tags, bookmark_tags."""
        init_db()
        conn = sqlite3.connect(str(tmp_db))
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = sorted(row[0] for row in cursor.fetchall())
        conn.close()
        assert tables == ["bookmark_tags", "bookmarks", "collections", "tags"]

    def test_creates_three_indexes(self, tmp_db):
        """init_db() creates the 3 required indexes."""
        init_db()
        conn = sqlite3.connect(str(tmp_db))
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND sql IS NOT NULL ORDER BY name"
        )
        indexes = [row[0] for row in cursor.fetchall()]
        conn.close()
        expected = [
            "idx_bookmark_tags_tag",
            "idx_bookmarks_collection",
            "idx_bookmarks_favourite",
        ]
        assert indexes == expected


class TestSeedIdempotency:
    def test_double_seed_no_duplicates(self, tmp_db):
        """Running seed_demo_data twice must not duplicate records."""
        init_db()
        seed_demo_data(str(tmp_db))
        seed_demo_data(str(tmp_db))
        conn = sqlite3.connect(str(tmp_db))
        collections = conn.execute("SELECT COUNT(*) FROM collections").fetchone()[0]
        bookmarks = conn.execute("SELECT COUNT(*) FROM bookmarks").fetchone()[0]
        tags = conn.execute("SELECT COUNT(*) FROM tags").fetchone()[0]
        bookmark_tags = conn.execute("SELECT COUNT(*) FROM bookmark_tags").fetchone()[0]
        conn.close()
        assert collections == 3
        assert bookmarks == 15
        assert tags == 10
        assert bookmark_tags >= 15


class TestSeedCounts:
    def test_seed_produces_expected_counts(self, tmp_db):
        """Seed produces exactly 3 collections, 15 bookmarks, 4 favourites."""
        init_db()
        seed_demo_data(str(tmp_db))
        conn = sqlite3.connect(str(tmp_db))
        collections = conn.execute("SELECT COUNT(*) FROM collections").fetchone()[0]
        bookmarks = conn.execute("SELECT COUNT(*) FROM bookmarks").fetchone()[0]
        favourites = conn.execute(
            "SELECT COUNT(*) FROM bookmarks WHERE is_favourite = 1"
        ).fetchone()[0]
        conn.close()
        assert collections == 3
        assert bookmarks == 15
        assert favourites == 4
