"""Integration tests for the CLI layer.

Uses the fresh_todo fixture from conftest.py for isolated per-test databases.
NO_COLOR=1 is set globally for all tests to avoid ANSI in captured output.
"""
from __future__ import annotations

import sys
import types

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run(monkeypatch, fresh_todo, argv: list[str]) -> tuple[int, str, str]:
    """Run main(argv) with a fresh module import; return (exit_code, stdout, stderr)."""
    # Purge cached modules so cli picks up fresh service/db bound to tmp DB
    for mod_name in list(sys.modules):
        if mod_name == "todo" or mod_name.startswith("todo."):
            del sys.modules[mod_name]

    from todo.db import init_db
    import todo.cli as cli_mod

    init_db()
    return cli_mod.main(argv)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def no_color(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")


# ---------------------------------------------------------------------------
# Parser construction
# ---------------------------------------------------------------------------


def test_parser_builds():
    """Parser can be constructed without error."""
    for mod_name in list(sys.modules):
        if mod_name == "todo" or mod_name.startswith("todo."):
            del sys.modules[mod_name]
    import todo.cli as cli_mod

    parser = cli_mod._build_parser()
    assert parser is not None


def test_parser_subcommands():
    """All expected subcommands are registered."""
    for mod_name in list(sys.modules):
        if mod_name == "todo" or mod_name.startswith("todo."):
            del sys.modules[mod_name]
    import todo.cli as cli_mod

    parser = cli_mod._build_parser()
    args = parser.parse_args(["add", "Test title"])
    assert args.command == "add"
    assert args.title == "Test title"
    assert args.priority == "medium"


# ---------------------------------------------------------------------------
# add command
# ---------------------------------------------------------------------------


def test_add_minimal(fresh_todo, monkeypatch, capsys):
    for mod_name in list(sys.modules):
        if mod_name == "todo" or mod_name.startswith("todo."):
            del sys.modules[mod_name]
    from todo.db import init_db
    import todo.cli as cli_mod

    init_db()
    rc = cli_mod.main(["add", "Buy milk"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Buy milk" in out
    assert "#1" in out


def test_add_full_options(fresh_todo, monkeypatch, capsys):
    for mod_name in list(sys.modules):
        if mod_name == "todo" or mod_name.startswith("todo."):
            del sys.modules[mod_name]
    from todo.db import init_db
    import todo.cli as cli_mod

    init_db()
    rc = cli_mod.main([
        "add", "Write report",
        "--description", "Monthly summary",
        "--priority", "high",
        "--due-date", "2026-12-31",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Write report" in out


def test_add_persists(fresh_todo, monkeypatch, capsys):
    """After add, list should show the new item."""
    for mod_name in list(sys.modules):
        if mod_name == "todo" or mod_name.startswith("todo."):
            del sys.modules[mod_name]
    from todo.db import init_db
    import todo.cli as cli_mod

    init_db()
    cli_mod.main(["add", "Persistent item"])
    rc = cli_mod.main(["list"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Persistent item" in out


def test_add_invalid_priority_returns_nonzero(fresh_todo, monkeypatch, capsys):
    for mod_name in list(sys.modules):
        if mod_name == "todo" or mod_name.startswith("todo."):
            del sys.modules[mod_name]
    from todo.db import init_db
    import todo.cli as cli_mod

    init_db()
    with pytest.raises(SystemExit) as exc_info:
        cli_mod.main(["add", "Bad priority", "--priority", "urgent"])
    assert exc_info.value.code != 0


# ---------------------------------------------------------------------------
# list command
# ---------------------------------------------------------------------------


def test_list_empty(fresh_todo, monkeypatch, capsys):
    for mod_name in list(sys.modules):
        if mod_name == "todo" or mod_name.startswith("todo."):
            del sys.modules[mod_name]
    from todo.db import init_db
    import todo.cli as cli_mod

    init_db()
    rc = cli_mod.main(["list"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "No todos found" in out


def test_list_filter_status(fresh_todo, monkeypatch, capsys):
    for mod_name in list(sys.modules):
        if mod_name == "todo" or mod_name.startswith("todo."):
            del sys.modules[mod_name]
    from todo.db import init_db
    import todo.cli as cli_mod

    init_db()
    cli_mod.main(["add", "Task A"])
    cli_mod.main(["add", "Task B"])
    cli_mod.main(["done", "1"])
    capsys.readouterr()  # discard previous output

    rc = cli_mod.main(["list", "--status", "pending"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Task B" in out
    assert "Task A" not in out


def test_list_filter_priority(fresh_todo, monkeypatch, capsys):
    for mod_name in list(sys.modules):
        if mod_name == "todo" or mod_name.startswith("todo."):
            del sys.modules[mod_name]
    from todo.db import init_db
    import todo.cli as cli_mod

    init_db()
    cli_mod.main(["add", "High task", "--priority", "high"])
    cli_mod.main(["add", "Low task", "--priority", "low"])
    capsys.readouterr()

    rc = cli_mod.main(["list", "--priority", "high"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "High task" in out
    assert "Low task" not in out


def test_list_combined_filters(fresh_todo, monkeypatch, capsys):
    for mod_name in list(sys.modules):
        if mod_name == "todo" or mod_name.startswith("todo."):
            del sys.modules[mod_name]
    from todo.db import init_db
    import todo.cli as cli_mod

    init_db()
    cli_mod.main(["add", "High pending", "--priority", "high"])
    cli_mod.main(["add", "High done", "--priority", "high"])
    cli_mod.main(["done", "2"])
    capsys.readouterr()

    rc = cli_mod.main(["list", "--status", "pending", "--priority", "high"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "High pending" in out
    assert "High done" not in out


# ---------------------------------------------------------------------------
# done command
# ---------------------------------------------------------------------------


def test_done_transitions_status(fresh_todo, monkeypatch, capsys):
    for mod_name in list(sys.modules):
        if mod_name == "todo" or mod_name.startswith("todo."):
            del sys.modules[mod_name]
    from todo.db import init_db
    import todo.cli as cli_mod

    init_db()
    cli_mod.main(["add", "Finish me"])
    capsys.readouterr()

    rc = cli_mod.main(["done", "1"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "done" in out.lower() or "#1" in out

    # Verify via list
    cli_mod.main(["list", "--status", "done"])
    out = capsys.readouterr().out
    assert "Finish me" in out


def test_done_missing_id_returns_nonzero(fresh_todo, monkeypatch, capsys):
    for mod_name in list(sys.modules):
        if mod_name == "todo" or mod_name.startswith("todo."):
            del sys.modules[mod_name]
    from todo.db import init_db
    import todo.cli as cli_mod

    init_db()
    rc = cli_mod.main(["done", "9999"])
    assert rc != 0
    err = capsys.readouterr().err
    assert "9999" in err or "not found" in err.lower()


# ---------------------------------------------------------------------------
# delete command
# ---------------------------------------------------------------------------


def test_delete_removes_todo(fresh_todo, monkeypatch, capsys):
    for mod_name in list(sys.modules):
        if mod_name == "todo" or mod_name.startswith("todo."):
            del sys.modules[mod_name]
    from todo.db import init_db
    import todo.cli as cli_mod

    init_db()
    cli_mod.main(["add", "To be deleted"])
    capsys.readouterr()

    rc = cli_mod.main(["delete", "1"])
    assert rc == 0

    cli_mod.main(["list"])
    out = capsys.readouterr().out
    assert "To be deleted" not in out


def test_delete_missing_id_returns_nonzero(fresh_todo, monkeypatch, capsys):
    for mod_name in list(sys.modules):
        if mod_name == "todo" or mod_name.startswith("todo."):
            del sys.modules[mod_name]
    from todo.db import init_db
    import todo.cli as cli_mod

    init_db()
    rc = cli_mod.main(["delete", "9999"])
    assert rc != 0
    err = capsys.readouterr().err
    assert "9999" in err or "not found" in err.lower()


# ---------------------------------------------------------------------------
# search command
# ---------------------------------------------------------------------------


def test_search_finds_match(fresh_todo, monkeypatch, capsys):
    for mod_name in list(sys.modules):
        if mod_name == "todo" or mod_name.startswith("todo."):
            del sys.modules[mod_name]
    from todo.db import init_db
    import todo.cli as cli_mod

    init_db()
    cli_mod.main(["add", "Buy groceries"])
    cli_mod.main(["add", "Write code"])
    capsys.readouterr()

    rc = cli_mod.main(["search", "groceries"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Buy groceries" in out
    assert "Write code" not in out


def test_search_no_match(fresh_todo, monkeypatch, capsys):
    for mod_name in list(sys.modules):
        if mod_name == "todo" or mod_name.startswith("todo."):
            del sys.modules[mod_name]
    from todo.db import init_db
    import todo.cli as cli_mod

    init_db()
    cli_mod.main(["add", "Buy milk"])
    capsys.readouterr()

    rc = cli_mod.main(["search", "xyz_not_found"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "No todos found" in out


def test_search_case_insensitive(fresh_todo, monkeypatch, capsys):
    for mod_name in list(sys.modules):
        if mod_name == "todo" or mod_name.startswith("todo."):
            del sys.modules[mod_name]
    from todo.db import init_db
    import todo.cli as cli_mod

    init_db()
    cli_mod.main(["add", "Uppercase Title"])
    capsys.readouterr()

    rc = cli_mod.main(["search", "uppercase"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Uppercase Title" in out


# ---------------------------------------------------------------------------
# stats command
# ---------------------------------------------------------------------------


def test_stats_empty_db(fresh_todo, monkeypatch, capsys):
    for mod_name in list(sys.modules):
        if mod_name == "todo" or mod_name.startswith("todo."):
            del sys.modules[mod_name]
    from todo.db import init_db
    import todo.cli as cli_mod

    init_db()
    rc = cli_mod.main(["stats"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Total" in out
    assert "0" in out


def test_stats_counts(fresh_todo, monkeypatch, capsys):
    for mod_name in list(sys.modules):
        if mod_name == "todo" or mod_name.startswith("todo."):
            del sys.modules[mod_name]
    from todo.db import init_db
    import todo.cli as cli_mod

    init_db()
    cli_mod.main(["add", "Task 1", "--priority", "high"])
    cli_mod.main(["add", "Task 2", "--priority", "low"])
    cli_mod.main(["add", "Task 3"])
    cli_mod.main(["done", "1"])
    capsys.readouterr()

    rc = cli_mod.main(["stats"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Total" in out
    assert "3" in out
