"""Pydantic v2 models for the Snippet Vault API."""
from __future__ import annotations

from pydantic import BaseModel, Field


class SnippetCreate(BaseModel):
    title: str
    code: str
    language: str
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    is_public: bool = True


class SnippetResponse(BaseModel):
    id: str
    title: str
    code: str
    language: str
    description: str | None
    tags: list[str]
    is_public: bool
    view_count: int
    created_at: str
    updated_at: str


class SnippetUpdate(BaseModel):
    title: str | None = None
    code: str | None = None
    language: str | None = None
    description: str | None = None
    is_public: bool | None = None
    tags: list[str] | None = None


class TagResponse(BaseModel):
    name: str
    snippet_count: int


class LanguageStats(BaseModel):
    language: str
    snippet_count: int
