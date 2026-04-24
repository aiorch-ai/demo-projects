"""Pytest fixtures for Weather Dashboard API integration tests.

DATABASE_URL is set per-test BEFORE importing any `app.*` module so that lazy
env resolution picks up the temp path. Each test gets a fresh database and a
freshly seeded dataset.
"""
from __future__ import annotations

import sys

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def db_path(tmp_path, monkeypatch) -> str:
    """Fresh sqlite file per test; DATABASE_URL env var points to it."""
    path = tmp_path / "weather.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{path}")
    return str(path)


@pytest.fixture
def client(db_path) -> TestClient:
    """TestClient bound to an isolated, freshly seeded database."""
    # Purge any cached app.* modules so DATABASE_URL is re-evaluated.
    for mod_name in list(sys.modules):
        if mod_name == "app" or mod_name.startswith("app."):
            del sys.modules[mod_name]

    from app.database import init_db
    from app.main import app
    from app.seed import seed_demo_data

    init_db()
    seed_demo_data(db_path)

    with TestClient(app) as tc:
        yield tc
