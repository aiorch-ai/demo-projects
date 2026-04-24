Build a simple Todo CLI application in Python inside the `todo-app/` directory.

## Agent 1 — Core Logic (HIGH difficulty)
Build the core todo engine with SQLite persistence:
- `todo-app/todo/db.py` — SQLite connection, schema creation (todos table: id, title, description, priority, status, created_at, due_date)
- `todo-app/todo/models.py` — Pydantic models for Todo, TodoCreate, TodoUpdate
- `todo-app/todo/service.py` — CRUD operations: add, list (with filters by status/priority), update, delete, search by keyword
- `todo-app/todo/__init__.py`
- `todo-app/tests/test_service.py` — Unit tests for all CRUD operations and edge cases

## Agent 2 — CLI Interface (MEDIUM difficulty)
Build the CLI using Python's argparse:
- `todo-app/todo/cli.py` — Commands: add, list, done, delete, search, stats
- `todo-app/todo/display.py` — Formatted table output with colors (using ANSI codes, no external deps)
- `todo-app/tests/test_cli.py` — Tests for CLI argument parsing
- Depends on Agent 1

## Agent 3 — Documentation & Setup (LOW difficulty)
- `todo-app/README.md` — Usage examples, installation instructions
- `todo-app/requirements.txt` — Dependencies (just pydantic)
- `todo-app/setup.py` — Basic setuptools config with console_scripts entry point
- No dependencies on other agents
