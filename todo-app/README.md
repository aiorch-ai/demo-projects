# Todo App

A lightweight command-line todo manager backed by SQLite.

## Overview

This is a simple yet effective todo management tool that stores tasks locally in an SQLite database. Each todo includes a title, description, priority level, and status tracking.

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Install the application in development mode:
   ```bash
   pip install -e .
   ```

The `todo` command will now be available in your terminal.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TODO_DB_PATH` | Path to the SQLite database file | `~/.todo/todos.db` |
| `NO_COLOR` | Disable ANSI color codes in output | (colors enabled by default) |

## Usage

### Commands

| Command | Arguments | Description |
|---------|-----------|-------------|
| `add` | `--title TITLE [--description DESC] [--priority PRIORITY] [--due-date DATE]` | Add a new todo item |
| `list` | `[--status STATUS] [--priority PRIORITY]` | List all todos (optionally filtered) |
| `done` | `ID` | Mark a todo as done |
| `delete` | `ID` | Delete a todo by ID |
| `search` | `KEYWORD` | Search todos by keyword in title and description |
| `stats` | (none) | Display statistics about todos |

### Examples

**Add a todo:**
```bash
todo add --title "Buy groceries" --priority high
todo add --title "Project draft" --description "Complete project proposal" --due-date 2026-05-01
```

**List todos:**
```bash
todo list
todo list --status pending
todo list --priority high
```

**Mark a todo as done:**
```bash
todo done 1
```

**Delete a todo:**
```bash
todo delete 2
```

**Search todos:**
```bash
todo search "project"
```

**View statistics:**
```bash
todo stats
```

## Running Tests

```bash
pytest tests/ -v
```

Tests use a temporary SQLite database per test case for isolation.

## Notes

- The `todo` binary name may conflict with other `todo` applications on your development machine. If this occurs, the last installed package with a `todo` console script will be used. Consider using a virtual environment to avoid conflicts.
- The database file is stored in `~/.todo/` by default. You can override this location with the `TODO_DB_PATH` environment variable.
- ANSI color codes are automatically disabled when piping output or when the `NO_COLOR` environment variable is set.
