"""Search endpoint under /api/bookmarks/search."""

import sqlite3

from fastapi import APIRouter, Depends, Query

from app.database import get_db
from app.models import BookmarkResponse
from app.services.search import search_bookmarks

router = APIRouter(prefix="/api/bookmarks", tags=["search"])


@router.get("/search", response_model=list[BookmarkResponse])
def search(
    q: str = Query(..., description="Search query (matched against title, url, description)"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: sqlite3.Connection = Depends(get_db),
) -> list[BookmarkResponse]:
    results = search_bookmarks(db, q, limit=limit, offset=offset)
    return [BookmarkResponse(**row) for row in results]
