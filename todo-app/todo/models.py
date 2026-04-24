"""Pydantic v2 models for the Todo CLI."""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class TodoCreate(BaseModel):
    title: str
    description: str | None = Field(default=None, max_length=4096)
    priority: Literal["low", "medium", "high"] = "medium"
    due_date: date | None = None


class TodoUpdate(BaseModel):
    title: str | None = None
    description: str | None = Field(default=None, max_length=4096)
    priority: Literal["low", "medium", "high"] | None = None
    status: Literal["pending", "done"] | None = None
    due_date: date | None = None


class Todo(BaseModel):
    id: int
    title: str
    description: str | None
    priority: Literal["low", "medium", "high"]
    status: Literal["pending", "done"]
    created_at: str
    due_date: str | None
