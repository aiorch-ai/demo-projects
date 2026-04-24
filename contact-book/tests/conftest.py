from __future__ import annotations

import sys

import pytest


@pytest.fixture
def db_path(tmp_path, monkeypatch) -> str:
    path = tmp_path / "contacts.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{path}")
    return str(path)


@pytest.fixture
def db(db_path) -> str:
    for mod_name in list(sys.modules):
        if mod_name == "contacts" or mod_name.startswith("contacts."):
            del sys.modules[mod_name]

    from contacts.db import init_db

    init_db()
    return db_path


# Backward-compatible alias used by earlier test modules.
@pytest.fixture
def fresh_db(db) -> str:
    return db
