"""Bookmark export and import services."""
from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime


def _row_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "url": row["url"],
        "title": row["title"],
        "description": row["description"],
        "collection_id": row["collection_id"],
        "is_favourite": bool(row["is_favourite"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _populate_tags(db: sqlite3.Connection, bookmark: dict) -> dict:
    tag_rows = db.execute(
        "SELECT tag_name FROM bookmark_tags WHERE bookmark_id = ?",
        (bookmark["id"],),
    ).fetchall()
    bookmark["tags"] = [t["tag_name"] for t in tag_rows]
    return bookmark


def export_bookmarks(db: sqlite3.Connection, collection_id: str | None = None) -> dict:
    """Export bookmarks (optionally filtered by collection) with tags populated."""
    if collection_id is not None:
        rows = db.execute(
            "SELECT * FROM bookmarks WHERE collection_id = ? ORDER BY created_at DESC",
            (collection_id,),
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM bookmarks ORDER BY created_at DESC"
        ).fetchall()

    bookmarks = [_populate_tags(db, _row_to_dict(row)) for row in rows]
    return {
        "bookmarks": bookmarks,
        "exported_at": datetime.utcnow().isoformat(),
        "count": len(bookmarks),
    }


def import_bookmarks(db: sqlite3.Connection, data: dict) -> dict:
    """Import bookmarks from exported JSON.

    Skips bookmarks whose URL already exists. If a bookmark references a
    collection_id that is not present in the target database, the reference
    is nulled. All inserts run inside a single transaction.
    """
    incoming = data.get("bookmarks", [])
    imported = 0
    skipped = 0

    with db:
        for item in incoming:
            url = item.get("url")
            if not url:
                skipped += 1
                continue

            existing = db.execute(
                "SELECT 1 FROM bookmarks WHERE url = ?", (url,)
            ).fetchone()
            if existing is not None:
                skipped += 1
                continue

            collection_id = item.get("collection_id")
            if collection_id is not None:
                col = db.execute(
                    "SELECT 1 FROM collections WHERE id = ?", (collection_id,)
                ).fetchone()
                if col is None:
                    collection_id = None

            bookmark_id = uuid.uuid4().hex
            db.execute(
                """
                INSERT INTO bookmarks (
                    id, url, title, description, collection_id, is_favourite
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    bookmark_id,
                    url,
                    item.get("title", ""),
                    item.get("description"),
                    collection_id,
                    1 if item.get("is_favourite") else 0,
                ),
            )

            for tag_name in item.get("tags", []) or []:
                db.execute(
                    "INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,)
                )
                db.execute(
                    """
                    INSERT OR IGNORE INTO bookmark_tags (bookmark_id, tag_name)
                    VALUES (?, ?)
                    """,
                    (bookmark_id, tag_name),
                )
            imported += 1

    return {"imported": imported, "skipped": skipped}
