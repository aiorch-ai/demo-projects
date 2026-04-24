"""Pytest fixtures for Todo CLI integration tests.

TODO_DB_PATH is set per-test BEFORE importing any `todo.*` module so that lazy
env resolution picks up the temp path. Each test gets a fresh database.
"""
from __future__ import annotations

import sys

import pytest


@pytest.fixture
def db_path(tmp_path, monkeypatch) -> str:
    """Fresh sqlite file per test; TODO_DB_PATH env var points to it."""
    path = tmp_path / "todos.db"
    monkeypatch.setenv("TODO_DB_PATH", str(path))
    return str(path)


@pytest.fixture
def fresh_todo(db_path):
    """Freshly imported todo modules with an initialized database."""
    # Purge any cached todo.* modules so TODO_DB_PATH is re-evaluated.
    for mod_name in list(sys.modules):
        if mod_name == "todo" or mod_name.startswith("todo."):
            del sys.modules[mod_name]

    import types

    from todo.db import init_db
    from todo import models, service

    init_db()
    ns = types.SimpleNamespace()
    ns.service = service
    ns.models = models
    return ns
