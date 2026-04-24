"""Integration tests for the CLI presentation layer."""
from __future__ import annotations

from pathlib import Path
import sys

import pytest


CURRENT_TODO_APP = Path(__file__).resolve().parents[1]
CURRENT_TODO_PACKAGE = CURRENT_TODO_APP / "todo"


def _purge_todo_modules() -> None:
    for mod_name in list(sys.modules):
        if mod_name == "todo" or mod_name.startswith("todo."):
            del sys.modules[mod_name]


def _import_cli():
    _purge_todo_modules()

    import todo

    cli_path = str(CURRENT_TODO_PACKAGE)
    if cli_path not in todo.__path__:
        todo.__path__.append(cli_path)

    import todo.cli as cli_mod

    return cli_mod


@pytest.fixture(autouse=True)
def no_color(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")


def test_parser_builds():
    parser = _import_cli()._build_parser()
    assert parser is not None


def test_parser_subcommands():
    args = _import_cli()._build_parser().parse_args(["add", "Test title"])
    assert args.command == "add"
    assert args.title == "Test title"
    assert args.priority == "medium"


def test_add_minimal(fresh_todo, capsys):
    rc = _import_cli().main(["add", "Buy milk"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Buy milk" in out
    assert "#1" in out


def test_add_full_options(fresh_todo, capsys):
    rc = _import_cli().main(
        [
            "add",
            "Write report",
            "--description",
            "Monthly summary",
            "--priority",
            "high",
            "--due-date",
            "2026-12-31",
        ]
    )
    assert rc == 0
    assert "Write report" in capsys.readouterr().out


def test_add_persists(fresh_todo, capsys):
    cli_mod = _import_cli()
    cli_mod.main(["add", "Persistent item"])
    rc = cli_mod.main(["list"])
    assert rc == 0
    assert "Persistent item" in capsys.readouterr().out


def test_add_invalid_priority_returns_nonzero(fresh_todo, capsys):
    rc = _import_cli().main(["add", "Bad priority", "--priority", "urgent"])
    captured = capsys.readouterr()
    assert rc != 0
    assert "invalid choice" in captured.err


def test_list_empty(fresh_todo, capsys):
    rc = _import_cli().main(["list"])
    assert rc == 0
    assert "No todos found" in capsys.readouterr().out


def test_list_filter_status(fresh_todo, capsys):
    cli_mod = _import_cli()
    cli_mod.main(["add", "Task A"])
    cli_mod.main(["add", "Task B"])
    cli_mod.main(["done", "1"])
    capsys.readouterr()

    rc = cli_mod.main(["list", "--status", "pending"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Task B" in out
    assert "Task A" not in out


def test_list_filter_priority(fresh_todo, capsys):
    cli_mod = _import_cli()
    cli_mod.main(["add", "High task", "--priority", "high"])
    cli_mod.main(["add", "Low task", "--priority", "low"])
    capsys.readouterr()

    rc = cli_mod.main(["list", "--priority", "high"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "High task" in out
    assert "Low task" not in out


def test_done_transitions_status(fresh_todo, capsys):
    cli_mod = _import_cli()
    cli_mod.main(["add", "Finish me"])
    capsys.readouterr()

    rc = cli_mod.main(["done", "1"])
    assert rc == 0
    assert "done" in capsys.readouterr().out.lower()

    cli_mod.main(["list", "--status", "done"])
    assert "Finish me" in capsys.readouterr().out


def test_done_missing_id_returns_nonzero(fresh_todo, capsys):
    rc = _import_cli().main(["done", "9999"])
    assert rc != 0
    err = capsys.readouterr().err
    assert "9999" in err or "not found" in err.lower()


def test_delete_removes_todo(fresh_todo, capsys):
    cli_mod = _import_cli()
    cli_mod.main(["add", "To be deleted"])
    capsys.readouterr()

    rc = cli_mod.main(["delete", "1"])
    assert rc == 0

    cli_mod.main(["list"])
    assert "To be deleted" not in capsys.readouterr().out


def test_delete_missing_id_returns_nonzero(fresh_todo, capsys):
    rc = _import_cli().main(["delete", "9999"])
    assert rc != 0
    err = capsys.readouterr().err
    assert "9999" in err or "not found" in err.lower()


def test_search_finds_match(fresh_todo, capsys):
    cli_mod = _import_cli()
    cli_mod.main(["add", "Buy groceries"])
    cli_mod.main(["add", "Write code"])
    capsys.readouterr()

    rc = cli_mod.main(["search", "groceries"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Buy groceries" in out
    assert "Write code" not in out


def test_search_no_match(fresh_todo, capsys):
    cli_mod = _import_cli()
    cli_mod.main(["add", "Buy milk"])
    capsys.readouterr()

    rc = _import_cli().main(["search", "xyz_not_found"])
    assert rc == 0
    assert "No todos found" in capsys.readouterr().out


def test_stats_counts(fresh_todo, capsys):
    cli_mod = _import_cli()
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
