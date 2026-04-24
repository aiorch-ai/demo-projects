"""CRUD service for todos."""
from __future__ import annotations

from todo.db import get_db
from todo.models import Todo, TodoCreate, TodoUpdate


def _row_to_todo(row: sqlite3.Row) -> Todo:
    return Todo(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        priority=row["priority"],
        status=row["status"],
        created_at=row["created_at"],
        due_date=row["due_date"],
    )


import sqlite3  # noqa: E402


def add(todo_create: TodoCreate) -> Todo:
    with get_db() as db:
        cursor = db.execute(
            """
            INSERT INTO todos (title, description, priority, due_date)
            VALUES (?, ?, ?, ?)
            """,
            (
                todo_create.title,
                todo_create.description,
                todo_create.priority,
                todo_create.due_date.isoformat() if todo_create.due_date else None,
            ),
        )
        todo_id = cursor.lastrowid
        row = db.execute(
            "SELECT * FROM todos WHERE id = ?", (todo_id,)
        ).fetchone()
        return _row_to_todo(row)


def list_todos(status: str | None = None, priority: str | None = None) -> list[Todo]:
    where_clauses: list[str] = []
    params: list[str | None] = []

    if status is not None:
        where_clauses.append("status = ?")
        params.append(status)
    if priority is not None:
        where_clauses.append("priority = ?")
        params.append(priority)

    query = "SELECT * FROM todos"
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    query += " ORDER BY created_at DESC"

    with get_db() as db:
        rows = db.execute(query, params).fetchall()
        return [_row_to_todo(row) for row in rows]


def update(todo_id: int, todo_update: TodoUpdate) -> Todo:
    fields: list[str] = []
    params: list[str | None] = []

    if todo_update.title is not None:
        fields.append("title = ?")
        params.append(todo_update.title)
    if todo_update.description is not None:
        fields.append("description = ?")
        params.append(todo_update.description)
    if todo_update.priority is not None:
        fields.append("priority = ?")
        params.append(todo_update.priority)
    if todo_update.status is not None:
        fields.append("status = ?")
        params.append(todo_update.status)
    if todo_update.due_date is not None:
        fields.append("due_date = ?")
        params.append(todo_update.due_date.isoformat())

    if not fields:
        with get_db() as db:
            row = db.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
            if row is None:
                raise ValueError(f"Todo with id {todo_id} not found")
            return _row_to_todo(row)

    params.append(todo_id)
    query = f"UPDATE todos SET {', '.join(fields)} WHERE id = ?"

    with get_db() as db:
        cursor = db.execute(query, params)
        if cursor.rowcount == 0:
            raise ValueError(f"Todo with id {todo_id} not found")
        row = db.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
        return _row_to_todo(row)


def delete(todo_id: int) -> None:
    with get_db() as db:
        cursor = db.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        if cursor.rowcount == 0:
            raise ValueError(f"Todo with id {todo_id} not found")


def mark_done(todo_id: int) -> Todo:
    with get_db() as db:
        cursor = db.execute(
            "UPDATE todos SET status = 'done' WHERE id = ?",
            (todo_id,),
        )
        if cursor.rowcount == 0:
            raise ValueError(f"Todo with id {todo_id} not found")
        row = db.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
        return _row_to_todo(row)


def search(keyword: str) -> list[Todo]:
    """Case-insensitive search across title and description.

    Escapes LIKE wildcards in the keyword so they are treated literally.
    """
    if not keyword:
        return []
    escaped = keyword.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    pattern = f"%{escaped}%"

    with get_db() as db:
        rows = db.execute(
            """
            SELECT * FROM todos
            WHERE (title LIKE ? ESCAPE '\\' OR description LIKE ? ESCAPE '\\')
            ORDER BY created_at DESC
            """,
            (pattern, pattern),
        ).fetchall()
        return [_row_to_todo(row) for row in rows]


def stats() -> dict:
    with get_db() as db:
        by_status = {
            row["status"]: row["count"]
            for row in db.execute(
                "SELECT status, COUNT(*) as count FROM todos GROUP BY status"
            ).fetchall()
        }
        by_priority = {
            row["priority"]: row["count"]
            for row in db.execute(
                "SELECT priority, COUNT(*) as count FROM todos GROUP BY priority"
            ).fetchall()
        }
        today = db.execute("SELECT date('now')").fetchone()[0]
        overdue_row = db.execute(
            "SELECT COUNT(*) as count FROM todos WHERE status = 'pending' AND due_date < ?",
            (today,),
        ).fetchone()
        overdue = overdue_row["count"] if overdue_row else 0

    return {
        "by_status": by_status,
        "by_priority": by_priority,
        "overdue": overdue,
    }
