"""Pydantic v2 models for the Bookmark Manager API."""
from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl


class BookmarkCreate(BaseModel):
    url: HttpUrl
    title: str
    description: str | None = None
    collection_id: str | None = None
    tags: list[str] = Field(default_factory=list)


class BookmarkUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    collection_id: str | None = None
    is_favourite: bool | None = None
    tags: list[str] | None = None


class BookmarkResponse(BaseModel):
    id: str
    url: str
    title: str
    description: str | None
    collection_id: str | None
    tags: list[str]
    is_favourite: bool
    created_at: str
    updated_at: str


class CollectionCreate(BaseModel):
    name: str
    description: str | None = None
    color: str = "#3b82f6"


class CollectionUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    color: str | None = None


class CollectionResponse(BaseModel):
    id: str
    name: str
    description: str | None
    color: str
    bookmark_count: int
    created_at: str


class TagResponse(BaseModel):
    name: str
    bookmark_count: int


class BookmarkExport(BaseModel):
    bookmarks: list[BookmarkResponse]
    exported_at: str
    count: int


class BookmarkImport(BaseModel):
    bookmarks: list[dict]
