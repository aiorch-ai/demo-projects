"""Search router — registered separately to avoid conflicts with the bookmarks router."""
from __future__ import annotations

from fastapi import APIRouter, Query

from app.database import get_db
from app.services.search import search_bookmarks

router = APIRouter(prefix="/api/bookmarks", tags=["search"])


@router.get("/search")
def search(
    q: str = Query(..., description="Search query matched against title, url, description"),
    limit: int = Query(50, ge=0),
    offset: int = Query(0, ge=0),
) -> list[dict]:
    with get_db() as db:
        return search_bookmarks(db, q, limit=limit, offset=offset)
