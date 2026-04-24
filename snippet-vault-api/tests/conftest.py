"""Pytest fixtures for Snippet Vault API integration tests."""
from __future__ import annotations

import sys

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def db_path(tmp_path, monkeypatch) -> str:
    path = tmp_path / "snippets.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{path}")
    return str(path)


@pytest.fixture
def client(db_path: str) -> TestClient:
    for mod_name in list(sys.modules):
        if mod_name == "app" or mod_name.startswith("app."):
            del sys.modules[mod_name]

    from app.database import init_db
    from app.main import app
    from app.seed import seed_demo_data

    init_db()
    seed_demo_data(db_path)

    with TestClient(app) as test_client:
        yield test_client
