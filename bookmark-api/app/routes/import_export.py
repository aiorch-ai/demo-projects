"""Import/export endpoints under /api/bookmarks."""

import sqlite3

from fastapi import APIRouter, Body, Depends, status

from app.database import get_db
from app.services.import_export import export_bookmarks, import_bookmarks

router = APIRouter(prefix="/api/bookmarks", tags=["import-export"])


@router.get("/export")
def export_endpoint(
    collection_id: str | None = None,
    db: sqlite3.Connection = Depends(get_db),
) -> dict:
    return export_bookmarks(db, collection_id=collection_id)


@router.post("/import", status_code=status.HTTP_200_OK)
def import_endpoint(
    payload: dict = Body(...),
    db: sqlite3.Connection = Depends(get_db),
) -> dict:
    return import_bookmarks(db, payload)
