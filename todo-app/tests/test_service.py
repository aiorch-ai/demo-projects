"""Tests for todo.service — uses real SQLite via tmp_path fixtures."""
from __future__ import annotations

from datetime import date, timedelta

import pytest
from pydantic import ValidationError


def test_add_minimal(fresh_todo):
    todo = fresh_todo.service.add(fresh_todo.models.TodoCreate(title="Buy milk"))
    assert todo.id is not None
    assert todo.title == "Buy milk"
    assert todo.description is None
    assert todo.priority == "medium"
    assert todo.status == "pending"
    assert todo.created_at is not None
    assert todo.due_date is None


def test_add_maximal(fresh_todo):
    todo = fresh_todo.service.add(
        fresh_todo.models.TodoCreate(
            title="Write tests",
            description="Cover all CRUD operations",
            priority="high",
            due_date=date(2025, 12, 31),
        )
    )
    assert todo.title == "Write tests"
    assert todo.description == "Cover all CRUD operations"
    assert todo.priority == "high"
    assert todo.due_date == "2025-12-31"


def test_list_empty(fresh_todo):
    todos = fresh_todo.service.list_todos()
    assert todos == []


def test_list_filtered_by_status(fresh_todo):
    fresh_todo.service.add(fresh_todo.models.TodoCreate(title="A"))
    fresh_todo.service.add(fresh_todo.models.TodoCreate(title="B"))
    fresh_todo.service.mark_done(1)

    pending = fresh_todo.service.list_todos(status="pending")
    done = fresh_todo.service.list_todos(status="done")
    assert len(pending) == 1
    assert pending[0].title == "B"
    assert len(done) == 1
    assert done[0].title == "A"


def test_list_filtered_by_priority(fresh_todo):
    fresh_todo.service.add(fresh_todo.models.TodoCreate(title="Low", priority="low"))
    fresh_todo.service.add(fresh_todo.models.TodoCreate(title="High", priority="high"))

    high = fresh_todo.service.list_todos(priority="high")
    assert len(high) == 1
    assert high[0].title == "High"


def test_list_combined_filters(fresh_todo):
    fresh_todo.service.add(fresh_todo.models.TodoCreate(title="A", priority="high"))
    fresh_todo.service.add(fresh_todo.models.TodoCreate(title="B", priority="high"))
    fresh_todo.service.mark_done(1)

    result = fresh_todo.service.list_todos(status="pending", priority="high")
    assert len(result) == 1
    assert result[0].title == "B"


def test_update_nonexistent_raises(fresh_todo):
    with pytest.raises(ValueError, match="not found"):
        fresh_todo.service.update(999, fresh_todo.models.TodoUpdate(title="Nope"))


def test_delete_nonexistent_raises(fresh_todo):
    with pytest.raises(ValueError, match="not found"):
        fresh_todo.service.delete(999)


def test_mark_done_idempotent(fresh_todo):
    fresh_todo.service.add(fresh_todo.models.TodoCreate(title="Task"))
    t1 = fresh_todo.service.mark_done(1)
    assert t1.status == "done"
    t2 = fresh_todo.service.mark_done(1)
    assert t2.status == "done"


def test_search_empty(fresh_todo):
    fresh_todo.service.add(fresh_todo.models.TodoCreate(title="Task"))
    assert fresh_todo.service.search("") == []


def test_search_special_chars(fresh_todo):
    fresh_todo.service.add(fresh_todo.models.TodoCreate(title="50% complete"))
    fresh_todo.service.add(fresh_todo.models.TodoCreate(title="under_score"))

    assert len(fresh_todo.service.search("%")) == 1
    assert len(fresh_todo.service.search("_")) == 1
    assert len(fresh_todo.service.search("50%")) == 1
    assert len(fresh_todo.service.search("under_")) == 1


def test_search_case_insensitive(fresh_todo):
    fresh_todo.service.add(fresh_todo.models.TodoCreate(title="Hello World"))
    assert len(fresh_todo.service.search("hello")) == 1
    assert len(fresh_todo.service.search("WORLD")) == 1
    assert len(fresh_todo.service.search("Hello World")) == 1


def test_stats_empty(fresh_todo):
    result = fresh_todo.service.stats()
    assert result == {"by_status": {}, "by_priority": {}, "overdue": 0}


def test_stats_with_overdue(fresh_todo):
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    fresh_todo.service.add(
        fresh_todo.models.TodoCreate(
            title="Overdue", due_date=date.fromisoformat(yesterday)
        )
    )
    fresh_todo.service.add(
        fresh_todo.models.TodoCreate(
            title="Future", due_date=date.today() + timedelta(days=1)
        )
    )
    fresh_todo.service.add(fresh_todo.models.TodoCreate(title="No date"))

    result = fresh_todo.service.stats()
    assert result["by_status"]["pending"] == 3
    assert result["by_priority"]["medium"] == 3
    assert result["overdue"] == 1


def test_due_date_in_past_flagged_overdue(fresh_todo):
    yesterday = date.today() - timedelta(days=1)
    fresh_todo.service.add(fresh_todo.models.TodoCreate(title="Old", due_date=yesterday))
    assert fresh_todo.service.stats()["overdue"] == 1


def test_pydantic_invalid_priority(fresh_todo):
    with pytest.raises(ValidationError):
        fresh_todo.models.TodoCreate(title="X", priority="invalid")  # type: ignore[arg-type]


def test_pydantic_invalid_status_in_update(fresh_todo):
    with pytest.raises(ValidationError):
        fresh_todo.models.TodoUpdate(status="invalid")  # type: ignore[arg-type]
