# Todo App

A lightweight command-line todo manager backed by SQLite.

## Overview

This project provides a local todo CLI for creating, listing, completing, deleting, searching, and summarizing tasks from your terminal.

## Installation

```bash
pip install -e .
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TODO_DB_PATH` | Path to the SQLite database file | `~/.todo/todos.db` |
| `NO_COLOR` | Disable ANSI color output | Disabled when set |

## Usage

| Command | Description | Example |
|---------|-------------|---------|
| `add` | Add a new todo item | `todo add "Buy milk"` |
| `list` | List todo items | `todo list` |
| `done` | Mark a todo as done | `todo done 1` |
| `delete` | Delete a todo item | `todo delete 1` |
| `search` | Search todo items | `todo search "milk"` |
| `stats` | Show todo statistics | `todo stats` |

### Examples

```bash
todo add "Buy milk"
todo list
todo done 1
todo delete 1
todo search "milk"
todo stats
```

## Running Tests

```bash
pytest tests/
```

## Notes

- The `todo` binary name may conflict with other tools named `todo` on development machines.
- If that conflict exists, use an isolated virtual environment so this package's `todo` entry point resolves predictably.
