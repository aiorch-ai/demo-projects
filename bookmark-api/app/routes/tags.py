"""Tag endpoints under /api/tags."""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.models import TagResponse

router = APIRouter(prefix="/api/tags", tags=["tags"])


@router.get("", response_model=list[TagResponse])
def list_tags(
    db: sqlite3.Connection = Depends(get_db),
) -> list[TagResponse]:
    rows = db.execute(
        """
        SELECT t.name, COUNT(bt.bookmark_id) AS bookmark_count
          FROM tags t
          LEFT JOIN bookmark_tags bt ON bt.tag_name = t.name
         GROUP BY t.name
         ORDER BY t.name
        """
    ).fetchall()
    return [
        TagResponse(name=r["name"], bookmark_count=int(r["bookmark_count"]))
        for r in rows
    ]


@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    name: str,
    db: sqlite3.Connection = Depends(get_db),
) -> None:
    cursor = db.execute("DELETE FROM tags WHERE name = ?", (name,))
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Tag not found")
