"""Full-text-ish search across bookmarks using parameterized SQL LIKE."""

import sqlite3


def _fetch_tags(db: sqlite3.Connection, bookmark_id: str) -> list[str]:
    rows = db.execute(
        "SELECT tag_name FROM bookmark_tags WHERE bookmark_id = ? ORDER BY tag_name",
        (bookmark_id,),
    ).fetchall()
    return [r["tag_name"] for r in rows]


def search_bookmarks(
    db: sqlite3.Connection,
    query: str,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    """Return bookmarks whose title, url, or description match the query.

    Uses parameterized SQL — never string-formats user input into the query.
    The result is shaped like BookmarkResponse (tags populated per row).
    """
    pattern = f"%{query}%"
    rows = db.execute(
        """
        SELECT *
          FROM bookmarks
         WHERE title LIKE ? COLLATE NOCASE
            OR url LIKE ? COLLATE NOCASE
            OR description LIKE ? COLLATE NOCASE
         ORDER BY created_at DESC, id DESC
         LIMIT ? OFFSET ?
        """,
        (pattern, pattern, pattern, limit, offset),
    ).fetchall()

    return [
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
