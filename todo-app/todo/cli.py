"""Command-line interface for the Todo app."""
from __future__ import annotations

import argparse
import sys

from pydantic import ValidationError

from todo import db, service
from todo.display import format_stats, format_todos
from todo.models import TodoCreate, TodoUpdate


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="todo",
        description="Simple todo list manager",
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    # add
    p_add = sub.add_parser("add", help="Add a new todo")
    p_add.add_argument("title", help="Todo title")
    p_add.add_argument("--description", "-d", default=None, help="Optional description")
    p_add.add_argument(
        "--priority",
        "-p",
        choices=["low", "medium", "high"],
        default="medium",
        help="Priority (default: medium)",
    )
    p_add.add_argument("--due-date", default=None, metavar="YYYY-MM-DD", help="Due date")

    # list
    p_list = sub.add_parser("list", help="List todos")
    p_list.add_argument(
        "--status", choices=["pending", "done"], default=None, help="Filter by status"
    )
    p_list.add_argument(
        "--priority",
        choices=["low", "medium", "high"],
        default=None,
        help="Filter by priority",
    )

    # done
    p_done = sub.add_parser("done", help="Mark a todo as done")
    p_done.add_argument("id", type=int, help="Todo ID")

    # delete
    p_del = sub.add_parser("delete", help="Delete a todo")
    p_del.add_argument("id", type=int, help="Todo ID")

    # search
    p_search = sub.add_parser("search", help="Search todos by keyword")
    p_search.add_argument("keyword", help="Search keyword")

    # stats
    sub.add_parser("stats", help="Show todo statistics")

    return parser


def _cmd_add(args: argparse.Namespace) -> int:
    try:
        todo_create = TodoCreate(
            title=args.title,
            description=args.description,
            priority=args.priority,
            due_date=args.due_date,
        )
    except ValidationError as exc:
        print(f"Validation error: {exc}", file=sys.stderr)
        return 1

    try:
        todo = service.add(todo_create)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Added todo #{todo.id}: {todo.title}")
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    todos = service.list_todos(status=args.status, priority=args.priority)
    print(format_todos(todos))
    return 0


def _cmd_done(args: argparse.Namespace) -> int:
    try:
        todo = service.mark_done(args.id)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Marked todo #{todo.id} as done: {todo.title}")
    return 0


def _cmd_delete(args: argparse.Namespace) -> int:
    try:
        service.delete(args.id)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Deleted todo #{args.id}")
    return 0


def _cmd_search(args: argparse.Namespace) -> int:
    todos = service.search(args.keyword)
    print(format_todos(todos))
    return 0


def _cmd_stats(args: argparse.Namespace) -> int:
    data = service.stats()
    print(format_stats(data))
    return 0


_COMMANDS = {
    "add": _cmd_add,
    "list": _cmd_list,
    "done": _cmd_done,
    "delete": _cmd_delete,
    "search": _cmd_search,
    "stats": _cmd_stats,
}


def main(argv: list[str] | None = None) -> int:
    db.init_db()
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 1
    handler = _COMMANDS[args.command]
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
