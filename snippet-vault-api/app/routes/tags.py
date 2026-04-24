"""Tag listing and deletion routes."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.database import get_db
from app.models import TagResponse


router = APIRouter(prefix="/api/tags", tags=["tags"])


@router.get("", response_model=list[TagResponse])
def list_tags() -> list[TagResponse]:
    with get_db() as db:
        rows = db.execute(
            """
            SELECT t.name, COUNT(st.snippet_id) AS snippet_count
            FROM tags t
            LEFT JOIN snippet_tags st ON st.tag_name = t.name
            GROUP BY t.name
            ORDER BY t.name ASC
            """
        ).fetchall()
    return [TagResponse(name=row["name"], snippet_count=row["snippet_count"]) for row in rows]


@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(name: str) -> None:
    with get_db() as db:
        cursor = db.execute("DELETE FROM tags WHERE name = ?", (name,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="tag not found")
