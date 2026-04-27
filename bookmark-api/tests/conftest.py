"""Shared pytest fixtures for the bookmark API tests.

Both fixtures are function-scoped so each test gets a pristine database
that has been initialized and seeded by the FastAPI lifespan.
"""

import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def db_path(tmp_path, monkeypatch):
    """Point DATABASE_URL at a per-test SQLite file.

    monkeypatch automatically restores the prior environment on teardown.
    """
    path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{path}")
    return str(path)


@pytest.fixture()
def client(db_path):
    """Yield a TestClient that has run the FastAPI lifespan (init_db + seed)."""
    from app.main import app

    with TestClient(app) as c:
        yield c
