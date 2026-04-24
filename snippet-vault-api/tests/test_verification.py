"""Integration verification tests for import, search, and startup seeding."""
from __future__ import annotations

import sqlite3
import sys

from fastapi.testclient import TestClient


def _reset_app_modules() -> None:
    for mod_name in list(sys.modules):
        if mod_name == "app" or mod_name.startswith("app."):
            del sys.modules[mod_name]


def test_app_import_sanity(db_path: str) -> None:
    _reset_app_modules()

    from app.main import app

    assert app.title == "Snippet Vault API"
    assert app.version == "1.0.0"


def test_search_fibonacci_endpoint(client: TestClient) -> None:
    response = client.get("/api/snippets/search", params={"q": "fibonacci"})

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["title"] == "Fibonacci with memoization"


def test_startup_seeds_empty_database_once(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "startup-snippets.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    _reset_app_modules()

    from app.main import app

    with TestClient(app):
        pass

    with sqlite3.connect(db_path) as conn:
        first_count = conn.execute("SELECT COUNT(*) FROM snippets").fetchone()[0]
    assert first_count == 10

    with TestClient(app):
        pass

    with sqlite3.connect(db_path) as conn:
        second_count = conn.execute("SELECT COUNT(*) FROM snippets").fetchone()[0]
    assert second_count == 10
