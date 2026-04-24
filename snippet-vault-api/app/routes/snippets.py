"""Snippet CRUD and search routes."""
from __future__ import annotations

import sqlite3
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from app.database import get_db
from app.models import SnippetCreate, SnippetResponse, SnippetUpdate


router = APIRouter(prefix="/api/snippets", tags=["snippets"])


def _normalize_tags(tags: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for tag in tags:
        clean_tag = tag.strip()
        if not clean_tag or clean_tag in seen:
            continue
        normalized.append(clean_tag)
        seen.add(clean_tag)
    return normalized


def _fetch_tags(db: sqlite3.Connection, snippet_ids: list[str]) -> dict[str, list[str]]:
    if not snippet_ids:
        return {}

    placeholders = ",".join("?" for _ in snippet_ids)
    rows = db.execute(
        f"""
        SELECT snippet_id, tag_name
        FROM snippet_tags
        WHERE snippet_id IN ({placeholders})
        ORDER BY tag_name ASC
        """,
        snippet_ids,
    ).fetchall()

    tag_map = {snippet_id: [] for snippet_id in snippet_ids}
    for row in rows:
        tag_map[row["snippet_id"]].append(row["tag_name"])
    return tag_map


def _row_to_snippet_response(
    row: sqlite3.Row,
    tag_map: dict[str, list[str]],
) -> SnippetResponse:
    return SnippetResponse(
        id=row["id"],
        title=row["title"],
        code=row["code"],
        language=row["language"],
        description=row["description"],
        tags=tag_map.get(row["id"], []),
        is_public=bool(row["is_public"]),
        view_count=row["view_count"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _fetch_snippet_or_404(db: sqlite3.Connection, snippet_id: str) -> sqlite3.Row:
    row = db.execute("SELECT * FROM snippets WHERE id = ?", (snippet_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="snippet not found")
    return row


def _ensure_tags(db: sqlite3.Connection, tag_names: list[str]) -> None:
    if not tag_names:
        return
    db.executemany(
        "INSERT OR IGNORE INTO tags (name) VALUES (?)",
        [(tag_name,) for tag_name in tag_names],
    )


def _replace_snippet_tags(db: sqlite3.Connection, snippet_id: str, tag_names: list[str]) -> None:
    db.execute("DELETE FROM snippet_tags WHERE snippet_id = ?", (snippet_id,))
    if not tag_names:
        return
    _ensure_tags(db, tag_names)
    db.executemany(
        "INSERT INTO snippet_tags (snippet_id, tag_name) VALUES (?, ?)",
        [(snippet_id, tag_name) for tag_name in tag_names],
    )


@router.post("", response_model=SnippetResponse, status_code=status.HTTP_201_CREATED)
def create_snippet(payload: SnippetCreate) -> SnippetResponse:
    snippet_id = str(uuid.uuid4())
    tag_names = _normalize_tags(payload.tags)

    with get_db() as db:
        db.execute(
            """
            INSERT INTO snippets (id, title, code, language, description, is_public)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                snippet_id,
                payload.title,
                payload.code,
                payload.language,
                payload.description,
                1 if payload.is_public else 0,
            ),
        )
        _replace_snippet_tags(db, snippet_id, tag_names)
        row = _fetch_snippet_or_404(db, snippet_id)
        tag_map = _fetch_tags(db, [snippet_id])
    return _row_to_snippet_response(row, tag_map)


@router.get("", response_model=list[SnippetResponse])
def list_snippets(
    language: str | None = None,
    tag: str | None = None,
    is_public: bool | None = None,
    limit: int = Query(default=20, ge=1),
    offset: int = Query(default=0, ge=0),
) -> list[SnippetResponse]:
    where: list[str] = []
    params: list[Any] = []

    if language is not None:
        where.append("s.language = ?")
        params.append(language)
    if tag is not None:
        where.append(
            """
            EXISTS (
                SELECT 1 FROM snippet_tags st
                WHERE st.snippet_id = s.id AND st.tag_name = ?
            )
            """.strip()
        )
        params.append(tag)
    if is_public is not None:
        where.append("s.is_public = ?")
        params.append(1 if is_public else 0)

    sql = "SELECT s.* FROM snippets s"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY s.created_at DESC, s.id ASC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_db() as db:
        rows = db.execute(sql, params).fetchall()
        snippet_ids = [row["id"] for row in rows]
        tag_map = _fetch_tags(db, snippet_ids)
    return [_row_to_snippet_response(row, tag_map) for row in rows]


@router.get("/search", response_model=list[SnippetResponse])
def search_snippets(
    q: str = Query(min_length=1),
    language: str | None = None,
    limit: int = Query(default=20, ge=1),
    offset: int = Query(default=0, ge=0),
) -> list[SnippetResponse]:
    where = ["(title LIKE ? OR description LIKE ? OR code LIKE ?)"]
    pattern = f"%{q}%"
    params: list[Any] = [pattern, pattern, pattern]

    if language is not None:
        where.append("language = ?")
        params.append(language)

    sql = (
        "SELECT * FROM snippets WHERE "
        + " AND ".join(where)
        + " ORDER BY created_at DESC, id ASC LIMIT ? OFFSET ?"
    )
    params.extend([limit, offset])

    with get_db() as db:
        rows = db.execute(sql, params).fetchall()
        snippet_ids = [row["id"] for row in rows]
        tag_map = _fetch_tags(db, snippet_ids)
    return [_row_to_snippet_response(row, tag_map) for row in rows]


@router.get("/{snippet_id}", response_model=SnippetResponse)
def get_snippet(snippet_id: str) -> SnippetResponse:
    with get_db() as db:
        _fetch_snippet_or_404(db, snippet_id)
        db.execute(
            "UPDATE snippets SET view_count = view_count + 1 WHERE id = ?",
            (snippet_id,),
        )
        row = _fetch_snippet_or_404(db, snippet_id)
        tag_map = _fetch_tags(db, [snippet_id])
    return _row_to_snippet_response(row, tag_map)


@router.put("/{snippet_id}", response_model=SnippetResponse)
def update_snippet(snippet_id: str, payload: SnippetUpdate) -> SnippetResponse:
    updates: list[str] = []
    params: list[Any] = []
    update_data = payload.model_dump(exclude_unset=True, exclude={"tags"})

    for field_name, value in update_data.items():
        if field_name == "is_public":
            value = 1 if value else 0
        updates.append(f"{field_name} = ?")
        params.append(value)

    with get_db() as db:
        _fetch_snippet_or_404(db, snippet_id)

        if updates:
            updates.append("updated_at = datetime('now')")
            params.append(snippet_id)
            db.execute(
                f"UPDATE snippets SET {', '.join(updates)} WHERE id = ?",
                params,
            )

        if payload.tags is not None:
            _replace_snippet_tags(db, snippet_id, _normalize_tags(payload.tags))

        row = _fetch_snippet_or_404(db, snippet_id)
        tag_map = _fetch_tags(db, [snippet_id])
    return _row_to_snippet_response(row, tag_map)


@router.delete("/{snippet_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_snippet(snippet_id: str) -> None:
    with get_db() as db:
        cursor = db.execute("DELETE FROM snippets WHERE id = ?", (snippet_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="snippet not found")
