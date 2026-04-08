"""Tests for app.database module."""

import os
import sqlite3
import tempfile

import pytest

from app.database import get_db, init_db


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
    def test_creates_all_tables(self, tmp_db):
        init_db()
        conn = sqlite3.connect(str(tmp_db))
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = sorted(row[0] for row in cursor.fetchall())
        conn.close()
        assert tables == ["clients", "invoices", "line_items", "tenants"]

    def test_creates_indexes(self, tmp_db):
        init_db()
        conn = sqlite3.connect(str(tmp_db))
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%' ORDER BY name"
        )
        indexes = [row[0] for row in cursor.fetchall()]
        conn.close()
        expected = [
            "idx_clients_tenant",
            "idx_invoices_client",
            "idx_invoices_due_date",
            "idx_invoices_status",
            "idx_invoices_tenant",
            "idx_line_items_invoice",
        ]
        assert indexes == expected

    def test_wal_mode_enabled(self, tmp_db):
        init_db()
        conn = sqlite3.connect(str(tmp_db))
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        conn.close()
        assert mode == "wal"

    def test_file_permissions(self, tmp_db):
        init_db()
        stat = os.stat(tmp_db)
        assert oct(stat.st_mode & 0o777) == oct(0o600)

    def test_raises_if_database_url_not_set(self):
        old = os.environ.pop("DATABASE_URL", None)
        try:
            with pytest.raises(RuntimeError, match="DATABASE_URL"):
                init_db()
        finally:
            if old is not None:
                os.environ["DATABASE_URL"] = old

    def test_raises_if_database_url_empty(self):
        old = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = ""
        try:
            with pytest.raises(RuntimeError, match="DATABASE_URL"):
                init_db()
        finally:
            if old is None:
                os.environ.pop("DATABASE_URL", None)
            else:
                os.environ["DATABASE_URL"] = old

    def test_creates_parent_directories(self, tmp_path):
        db_file = tmp_path / "nested" / "deep" / "test.db"
        old = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = f"sqlite:///{db_file}"
        try:
            init_db()
            assert db_file.exists()
        finally:
            if old is None:
                os.environ.pop("DATABASE_URL", None)
            else:
                os.environ["DATABASE_URL"] = old


class TestGetDb:
    def test_yields_connection_with_row_factory(self, tmp_db):
        init_db()
        gen = get_db()
        conn = next(gen)
        assert conn.row_factory is sqlite3.Row
        try:
            gen.send(None)
        except StopIteration:
            pass

    def test_foreign_keys_enabled(self, tmp_db):
        init_db()
        gen = get_db()
        conn = next(gen)
        fk = conn.execute("PRAGMA foreign_keys").fetchone()[0]
        try:
            gen.send(None)
        except StopIteration:
            pass
        assert fk == 1

    def test_wal_mode(self, tmp_db):
        init_db()
        gen = get_db()
        conn = next(gen)
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        try:
            gen.send(None)
        except StopIteration:
            pass
        assert mode == "wal"

    def test_commits_on_success(self, tmp_db):
        init_db()
        gen = get_db()
        conn = next(gen)
        conn.execute(
            "INSERT INTO tenants (id, name, api_key) VALUES (?, ?, ?)",
            ("t1", "Test Tenant", "key123"),
        )
        try:
            gen.send(None)
        except StopIteration:
            pass

        # Verify data was committed by opening a new connection
        verify = sqlite3.connect(str(tmp_db))
        row = verify.execute("SELECT name FROM tenants WHERE id='t1'").fetchone()
        verify.close()
        assert row is not None
        assert row[0] == "Test Tenant"

    def test_rollback_on_exception(self, tmp_db):
        init_db()
        gen = get_db()
        conn = next(gen)
        conn.execute(
            "INSERT INTO tenants (id, name, api_key) VALUES (?, ?, ?)",
            ("t2", "Rollback Tenant", "key456"),
        )
        try:
            gen.throw(ValueError("test error"))
        except ValueError:
            pass

        # Verify data was rolled back
        verify = sqlite3.connect(str(tmp_db))
        row = verify.execute("SELECT name FROM tenants WHERE id='t2'").fetchone()
        verify.close()
        assert row is None

    def test_raises_if_database_url_not_set(self):
        old = os.environ.pop("DATABASE_URL", None)
        try:
            with pytest.raises(RuntimeError, match="DATABASE_URL"):
                gen = get_db()
                next(gen)
        finally:
            if old is not None:
                os.environ["DATABASE_URL"] = old
