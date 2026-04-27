"""Bookmark CRUD endpoints under /api/bookmarks."""

import sqlite3
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.database import get_db
from app.models import BookmarkCreate, BookmarkResponse, BookmarkUpdate

router = APIRouter(prefix="/api/bookmarks", tags=["bookmarks"])


def _fetch_tags(db: sqlite3.Connection, bookmark_id: str) -> list[str]:
    rows = db.execute(
        "SELECT tag_name FROM bookmark_tags WHERE bookmark_id = ? ORDER BY tag_name",
        (bookmark_id,),
    ).fetchall()
    return [r["tag_name"] for r in rows]


def _row_to_response(db: sqlite3.Connection, row: sqlite3.Row) -> BookmarkResponse:
    return BookmarkResponse(
        id=row["id"],
        url=row["url"],
        title=row["title"],
        description=row["description"],
        collection_id=row["collection_id"],
        tags=_fetch_tags(db, row["id"]),
        is_favourite=bool(row["is_favourite"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _cleanup_orphan_tags(db: sqlite3.Connection) -> None:
    db.execute(
        "DELETE FROM tags WHERE name NOT IN (SELECT DISTINCT tag_name FROM bookmark_tags)"
    )


def _attach_tags(
    db: sqlite3.Connection, bookmark_id: str, tag_names: list[str]
) -> None:
    seen: set[str] = set()
    deduped: list[str] = []
    for name in tag_names:
        if name not in seen:
            seen.add(name)
            deduped.append(name)
    for name in deduped:
        db.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (name,))
        db.execute(
            "INSERT OR IGNORE INTO bookmark_tags (bookmark_id, tag_name) VALUES (?, ?)",
            (bookmark_id, name),
        )


@router.post("", response_model=BookmarkResponse, status_code=status.HTTP_201_CREATED)
def create_bookmark(
    payload: BookmarkCreate,
    db: sqlite3.Connection = Depends(get_db),
) -> BookmarkResponse:
    bookmark_id = str(uuid4())
    db.execute(
        """
        INSERT INTO bookmarks (id, url, title, description, collection_id, is_favourite)
        VALUES (?, ?, ?, ?, ?, 0)
        """,
        (
            bookmark_id,
            str(payload.url),
            payload.title,
            payload.description,
            payload.collection_id,
        ),
    )
    _attach_tags(db, bookmark_id, payload.tags)

    row = db.execute(
        "SELECT * FROM bookmarks WHERE id = ?", (bookmark_id,)
    ).fetchone()
    return _row_to_response(db, row)


@router.get("", response_model=list[BookmarkResponse])
def list_bookmarks(
    collection_id: str | None = None,
    tag: str | None = None,
    is_favourite: bool | None = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: sqlite3.Connection = Depends(get_db),
) -> list[BookmarkResponse]:
    clauses: list[str] = []
    params: list[object] = []
    join = ""

    if tag is not None:
        join = " JOIN bookmark_tags bt ON bt.bookmark_id = b.id"
        clauses.append("bt.tag_name = ?")
        params.append(tag)
    if collection_id is not None:
        clauses.append("b.collection_id = ?")
        params.append(collection_id)
    if is_favourite is not None:
        clauses.append("b.is_favourite = ?")
        params.append(1 if is_favourite else 0)

    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = (
        f"SELECT b.* FROM bookmarks b{join}{where} "
        f"ORDER BY b.created_at DESC, b.id DESC LIMIT ? OFFSET ?"
    )
    params.extend([limit, offset])

    rows = db.execute(sql, tuple(params)).fetchall()
    return [_row_to_response(db, r) for r in rows]


@router.get("/{bookmark_id}", response_model=BookmarkResponse)
def get_bookmark(
    bookmark_id: str,
    db: sqlite3.Connection = Depends(get_db),
) -> BookmarkResponse:
    row = db.execute(
        "SELECT * FROM bookmarks WHERE id = ?", (bookmark_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    return _row_to_response(db, row)


@router.put("/{bookmark_id}", response_model=BookmarkResponse)
def update_bookmark(
    bookmark_id: str,
    payload: BookmarkUpdate,
    db: sqlite3.Connection = Depends(get_db),
) -> BookmarkResponse:
    existing = db.execute(
        "SELECT id FROM bookmarks WHERE id = ?", (bookmark_id,)
    ).fetchone()
    if existing is None:
        raise HTTPException(status_code=404, detail="Bookmark not found")

    data = payload.model_dump(exclude_unset=True)
    tags = data.pop("tags", None) if "tags" in data else None
    has_tags_update = "tags" in payload.model_fields_set

    set_parts: list[str] = []
    values: list[object] = []
    for field, value in data.items():
        if field == "is_favourite":
            set_parts.append("is_favourite = ?")
            values.append(1 if value else 0)
        else:
            set_parts.append(f"{field} = ?")
            values.append(value)

    if set_parts:
        set_parts.append("updated_at = datetime('now')")
        values.append(bookmark_id)
        db.execute(
            f"UPDATE bookmarks SET {', '.join(set_parts)} WHERE id = ?",
            tuple(values),
        )
    elif has_tags_update:
        db.execute(
            "UPDATE bookmarks SET updated_at = datetime('now') WHERE id = ?",
            (bookmark_id,),
        )

    if has_tags_update:
        db.execute(
            "DELETE FROM bookmark_tags WHERE bookmark_id = ?", (bookmark_id,)
        )
        _attach_tags(db, bookmark_id, tags or [])
        _cleanup_orphan_tags(db)

    row = db.execute(
        "SELECT * FROM bookmarks WHERE id = ?", (bookmark_id,)
    ).fetchone()
    return _row_to_response(db, row)


@router.delete("/{bookmark_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bookmark(
    bookmark_id: str,
    db: sqlite3.Connection = Depends(get_db),
) -> None:
    cursor = db.execute("DELETE FROM bookmarks WHERE id = ?", (bookmark_id,))
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    _cleanup_orphan_tags(db)


@router.post("/{bookmark_id}/favourite", response_model=BookmarkResponse)
def toggle_favourite(
    bookmark_id: str,
    db: sqlite3.Connection = Depends(get_db),
) -> BookmarkResponse:
    cursor = db.execute(
        """
        UPDATE bookmarks
           SET is_favourite = 1 - is_favourite,
               updated_at = datetime('now')
         WHERE id = ?
        """,
        (bookmark_id,),
    )
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    row = db.execute(
        "SELECT * FROM bookmarks WHERE id = ?", (bookmark_id,)
    ).fetchone()
    return _row_to_response(db, row)
