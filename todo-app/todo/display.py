"""ANSI-colored table formatter for todo output.

Colors are suppressed when NO_COLOR is set or stdout is not a tty.
"""
from __future__ import annotations

import os
import sys

from todo.models import Todo

RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RESET = "\033[0m"


def _use_color() -> bool:
    return sys.stdout.isatty() and "NO_COLOR" not in os.environ


def _priority_color(priority: str) -> str:
    if not _use_color():
        return ""
    return {"high": RED, "medium": YELLOW, "low": GREEN}.get(priority, "")


def _status_color(status: str) -> str:
    if not _use_color():
        return ""
    return {"done": GREEN, "pending": YELLOW}.get(status, "")


def format_todos(todos: list[Todo]) -> str:
    if not todos:
        return "No todos found."

    reset = RESET if _use_color() else ""

    header = f"{'ID':<5} {'STATUS':<10} {'PRIORITY':<10} {'DUE DATE':<12} {'TITLE'}"
    sep = "-" * 70
    lines = [header, sep]

    for todo in todos:
        pc = _priority_color(todo.priority)
        sc = _status_color(todo.status)
        due = todo.due_date or ""
        priority_str = f"{pc}{todo.priority:<10}{reset}"
        status_str = f"{sc}{todo.status:<10}{reset}"
        lines.append(
            f"{todo.id:<5} {status_str} {priority_str} {due:<12} {todo.title}"
        )
        if todo.description:
            lines.append(f"      {todo.description}")

    return "\n".join(lines)


def format_stats(stats: dict) -> str:
    by_status = stats.get("by_status", {})
    by_priority = stats.get("by_priority", {})
    overdue = stats.get("overdue", 0)

    pending = by_status.get("pending", 0)
    done = by_status.get("done", 0)
    total = pending + done

    lines = [
        f"Total:    {total}",
        f"Pending:  {pending}",
        f"Done:     {done}",
        f"Overdue:  {overdue}",
        "",
        "By priority:",
        f"  High:   {by_priority.get('high', 0)}",
        f"  Medium: {by_priority.get('medium', 0)}",
        f"  Low:    {by_priority.get('low', 0)}",
    ]
    return "\n".join(lines)
