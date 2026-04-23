"""Tags router: list with counts, delete by name."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status

from app.database import get_db
from app.models import TagResponse


router = APIRouter(prefix="/api/tags", tags=["tags"])


@router.get("", response_model=list[TagResponse])
def list_tags() -> list[TagResponse]:
    with get_db() as db:
        rows = db.execute(
            "SELECT t.name AS name, COUNT(bt.bookmark_id) AS bookmark_count "
            "FROM tags t "
            "LEFT JOIN bookmark_tags bt ON bt.tag_name = t.name "
            "GROUP BY t.name ORDER BY t.name"
        ).fetchall()
    return [TagResponse(name=r["name"], bookmark_count=r["bookmark_count"]) for r in rows]


@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(name: str) -> Response:
    with get_db() as db:
        existing = db.execute("SELECT 1 FROM tags WHERE name = ?", (name,)).fetchone()
        if existing is None:
            raise HTTPException(status_code=404, detail="tag not found")
        db.execute("DELETE FROM tags WHERE name = ?", (name,))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
