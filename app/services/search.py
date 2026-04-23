"""Case-insensitive LIKE-based bookmark search."""
from __future__ import annotations

import sqlite3


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


def search_bookmarks(
    db: sqlite3.Connection,
    query: str,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    """Search bookmarks by title, URL, and description using LIKE with COLLATE NOCASE."""
    pattern = f"%{query}%"
    rows = db.execute(
        """
        SELECT *
        FROM bookmarks
        WHERE (
            title LIKE ? COLLATE NOCASE
            OR url LIKE ? COLLATE NOCASE
            OR description LIKE ? COLLATE NOCASE
        )
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
        """,
        (pattern, pattern, pattern, limit, offset),
    ).fetchall()

    results: list[dict] = []
    for row in rows:
        bookmark = _row_to_dict(row)
        tag_rows = db.execute(
            "SELECT tag_name FROM bookmark_tags WHERE bookmark_id = ?",
            (bookmark["id"],),
        ).fetchall()
        bookmark["tags"] = [t["tag_name"] for t in tag_rows]
        results.append(bookmark)
    return results
