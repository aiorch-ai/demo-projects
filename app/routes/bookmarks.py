"""Bookmarks router: CRUD + favourite toggle."""
from __future__ import annotations

import sqlite3
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Response, status

from app.database import get_db
from app.models import BookmarkCreate, BookmarkResponse, BookmarkUpdate


router = APIRouter(prefix="/api/bookmarks", tags=["bookmarks"])


def _row_to_response(row: sqlite3.Row, tags: list[str]) -> BookmarkResponse:
    return BookmarkResponse(
        id=row["id"],
        url=row["url"],
        title=row["title"],
        description=row["description"],
        collection_id=row["collection_id"],
        tags=tags,
        is_favourite=bool(row["is_favourite"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _fetch_tags(db: sqlite3.Connection, bookmark_id: str) -> list[str]:
    rows = db.execute(
        "SELECT tag_name FROM bookmark_tags WHERE bookmark_id = ? ORDER BY tag_name",
        (bookmark_id,),
    ).fetchall()
    return [r["tag_name"] for r in rows]


def _group_tags(db: sqlite3.Connection, bookmark_ids: list[str]) -> dict[str, list[str]]:
    if not bookmark_ids:
        return {}
    placeholders = ",".join("?" for _ in bookmark_ids)
    rows = db.execute(
        f"SELECT bookmark_id, tag_name FROM bookmark_tags "
        f"WHERE bookmark_id IN ({placeholders}) ORDER BY tag_name",
        bookmark_ids,
    ).fetchall()
    grouped: dict[str, list[str]] = {bid: [] for bid in bookmark_ids}
    for r in rows:
        grouped[r["bookmark_id"]].append(r["tag_name"])
    return grouped


def _insert_tags(db: sqlite3.Connection, bookmark_id: str, tags: list[str]) -> None:
    for tag in tags:
        db.execute("INSERT OR IGNORE INTO tags(name) VALUES (?)", (tag,))
        db.execute(
            "INSERT OR IGNORE INTO bookmark_tags(bookmark_id, tag_name) VALUES (?, ?)",
            (bookmark_id, tag),
        )


def _prune_orphan_tags(db: sqlite3.Connection) -> None:
    db.execute(
        "DELETE FROM tags WHERE name NOT IN (SELECT DISTINCT tag_name FROM bookmark_tags)"
    )


@router.post("", response_model=BookmarkResponse, status_code=status.HTTP_201_CREATED)
def create_bookmark(payload: BookmarkCreate) -> BookmarkResponse:
    bookmark_id = uuid.uuid4().hex
    url_str = str(payload.url)
    with get_db() as db:
        if payload.collection_id is not None:
            exists = db.execute(
                "SELECT 1 FROM collections WHERE id = ?", (payload.collection_id,)
            ).fetchone()
            if not exists:
                raise HTTPException(status_code=404, detail="collection not found")
        db.execute(
            "INSERT INTO bookmarks(id, url, title, description, collection_id) "
            "VALUES (?, ?, ?, ?, ?)",
            (bookmark_id, url_str, payload.title, payload.description, payload.collection_id),
        )
        _insert_tags(db, bookmark_id, payload.tags)
        row = db.execute(
            "SELECT * FROM bookmarks WHERE id = ?", (bookmark_id,)
        ).fetchone()
        tags = _fetch_tags(db, bookmark_id)
    return _row_to_response(row, tags)


@router.get("", response_model=list[BookmarkResponse])
def list_bookmarks(
    collection_id: str | None = None,
    tag: str | None = None,
    is_favourite: bool | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[BookmarkResponse]:
    where: list[str] = []
    params: list[Any] = []
    join = ""
    if tag is not None:
        join = "JOIN bookmark_tags bt ON bt.bookmark_id = b.id"
        where.append("bt.tag_name = ?")
        params.append(tag)
    if collection_id is not None:
        where.append("b.collection_id = ?")
        params.append(collection_id)
    if is_favourite is not None:
        where.append("b.is_favourite = ?")
        params.append(1 if is_favourite else 0)

    sql = f"SELECT b.* FROM bookmarks b {join}"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY b.created_at DESC, b.id LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_db() as db:
        rows = db.execute(sql, params).fetchall()
        ids = [r["id"] for r in rows]
        tag_map = _group_tags(db, ids)

    return [_row_to_response(r, tag_map.get(r["id"], [])) for r in rows]


@router.get("/{bookmark_id}", response_model=BookmarkResponse)
def get_bookmark(bookmark_id: str) -> BookmarkResponse:
    with get_db() as db:
        row = db.execute("SELECT * FROM bookmarks WHERE id = ?", (bookmark_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="bookmark not found")
        tags = _fetch_tags(db, bookmark_id)
    return _row_to_response(row, tags)


@router.put("/{bookmark_id}", response_model=BookmarkResponse)
def update_bookmark(bookmark_id: str, payload: BookmarkUpdate) -> BookmarkResponse:
    data = payload.model_dump(exclude_unset=True)
    with get_db() as db:
        existing = db.execute(
            "SELECT * FROM bookmarks WHERE id = ?", (bookmark_id,)
        ).fetchone()
        if existing is None:
            raise HTTPException(status_code=404, detail="bookmark not found")

        if "collection_id" in data and data["collection_id"] is not None:
            exists = db.execute(
                "SELECT 1 FROM collections WHERE id = ?", (data["collection_id"],)
            ).fetchone()
            if not exists:
                raise HTTPException(status_code=404, detail="collection not found")

        set_parts: list[str] = []
        values: list[Any] = []
        for field in ("title", "description", "collection_id", "is_favourite"):
            if field in data:
                value = data[field]
                if field == "is_favourite":
                    value = 1 if value else 0
                set_parts.append(f"{field} = ?")
                values.append(value)

        if set_parts or "tags" in data:
            set_parts.append("updated_at = datetime('now')")
            values.append(bookmark_id)
            db.execute(
                f"UPDATE bookmarks SET {', '.join(set_parts)} WHERE id = ?",
                values,
            )

        if "tags" in data and data["tags"] is not None:
            db.execute(
                "DELETE FROM bookmark_tags WHERE bookmark_id = ?", (bookmark_id,)
            )
            _insert_tags(db, bookmark_id, data["tags"])
            _prune_orphan_tags(db)

        row = db.execute(
            "SELECT * FROM bookmarks WHERE id = ?", (bookmark_id,)
        ).fetchone()
        tags = _fetch_tags(db, bookmark_id)

    return _row_to_response(row, tags)


@router.delete("/{bookmark_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bookmark(bookmark_id: str) -> Response:
    with get_db() as db:
        existing = db.execute(
            "SELECT 1 FROM bookmarks WHERE id = ?", (bookmark_id,)
        ).fetchone()
        if existing is None:
            raise HTTPException(status_code=404, detail="bookmark not found")
        db.execute("DELETE FROM bookmarks WHERE id = ?", (bookmark_id,))
        _prune_orphan_tags(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{bookmark_id}/favourite", response_model=BookmarkResponse)
def toggle_favourite(bookmark_id: str) -> BookmarkResponse:
    with get_db() as db:
        existing = db.execute(
            "SELECT * FROM bookmarks WHERE id = ?", (bookmark_id,)
        ).fetchone()
        if existing is None:
            raise HTTPException(status_code=404, detail="bookmark not found")
        new_value = 0 if existing["is_favourite"] else 1
        db.execute(
            "UPDATE bookmarks SET is_favourite = ?, updated_at = datetime('now') "
            "WHERE id = ?",
            (new_value, bookmark_id),
        )
        row = db.execute(
            "SELECT * FROM bookmarks WHERE id = ?", (bookmark_id,)
        ).fetchone()
        tags = _fetch_tags(db, bookmark_id)
    return _row_to_response(row, tags)
