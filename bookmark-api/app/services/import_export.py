"""Bookmark import/export services."""

import sqlite3
from datetime import datetime
from uuid import uuid4


def _fetch_tags(db: sqlite3.Connection, bookmark_id: str) -> list[str]:
    rows = db.execute(
        "SELECT tag_name FROM bookmark_tags WHERE bookmark_id = ? ORDER BY tag_name",
        (bookmark_id,),
    ).fetchall()
    return [r["tag_name"] for r in rows]


def export_bookmarks(
    db: sqlite3.Connection,
    collection_id: str | None = None,
) -> dict:
    """Return a dict with all bookmarks (optionally filtered by collection_id).

    The shape matches BookmarkExport: {bookmarks, exported_at, count}.
    Each bookmark dict includes tags joined via bookmark_tags.
    """
    if collection_id is None:
        rows = db.execute(
            "SELECT * FROM bookmarks ORDER BY created_at DESC, id DESC"
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM bookmarks WHERE collection_id = ? "
            "ORDER BY created_at DESC, id DESC",
            (collection_id,),
        ).fetchall()

    bookmarks = [
        {
            "id": r["id"],
            "url": r["url"],
            "title": r["title"],
            "description": r["description"],
            "collection_id": r["collection_id"],
            "tags": _fetch_tags(db, r["id"]),
            "is_favourite": bool(r["is_favourite"]),
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        }
        for r in rows
    ]

    return {
        "bookmarks": bookmarks,
        "exported_at": datetime.utcnow().isoformat(),
        "count": len(bookmarks),
    }


def import_bookmarks(db: sqlite3.Connection, data: dict) -> dict:
    """Import bookmarks from an export-shaped dict.

    For each bookmark in data['bookmarks']:
      - if a row with the same url already exists, skip it.
      - otherwise insert a new row with a fresh uuid4 id, preserving
        title/description/collection_id/is_favourite/created_at/updated_at
        when supplied. Tags are inserted via INSERT OR IGNORE.

    Returns {'imported': int, 'skipped': int}.
    """
    incoming = data.get("bookmarks") or []
    imported = 0
    skipped = 0

    for entry in incoming:
        url = entry.get("url")
        if not url:
            skipped += 1
            continue

        url = str(url)
        existing = db.execute(
            "SELECT 1 FROM bookmarks WHERE url = ?", (url,)
        ).fetchone()
        if existing is not None:
            skipped += 1
            continue

        new_id = str(uuid4())
        title = entry.get("title", "")
        description = entry.get("description")
        collection_id = entry.get("collection_id")
        is_favourite = 1 if entry.get("is_favourite") else 0
        created_at = entry.get("created_at")
        updated_at = entry.get("updated_at")

        if created_at and updated_at:
            db.execute(
                """
                INSERT INTO bookmarks
                    (id, url, title, description, collection_id, is_favourite,
                     created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_id,
                    url,
                    title,
                    description,
                    collection_id,
                    is_favourite,
                    created_at,
                    updated_at,
                ),
            )
        else:
            db.execute(
                """
                INSERT INTO bookmarks
                    (id, url, title, description, collection_id, is_favourite)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    new_id,
                    url,
                    title,
                    description,
                    collection_id,
                    is_favourite,
                ),
            )

        for tag in entry.get("tags") or []:
            db.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag,))
            db.execute(
                "INSERT OR IGNORE INTO bookmark_tags (bookmark_id, tag_name) VALUES (?, ?)",
                (new_id, tag),
            )

        imported += 1

    return {"imported": imported, "skipped": skipped}
