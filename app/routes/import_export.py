"""Import/Export router — registered separately to avoid conflicts with the bookmarks router."""
from __future__ import annotations

from fastapi import APIRouter, Body, Query

from app.database import get_db
from app.services.import_export import export_bookmarks, import_bookmarks

router = APIRouter(prefix="/api/bookmarks", tags=["import-export"])


@router.get("/export")
def export_all(collection_id: str | None = Query(None)) -> dict:
    with get_db() as db:
        return export_bookmarks(db, collection_id=collection_id)


@router.post("/import")
def import_all(payload: dict = Body(...)) -> dict:
    with get_db() as db:
        return import_bookmarks(db, payload)
