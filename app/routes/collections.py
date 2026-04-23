"""Collections router: CRUD with bookmark counts."""
from __future__ import annotations

import sqlite3
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Response, status

from app.database import get_db
from app.models import CollectionCreate, CollectionResponse, CollectionUpdate


router = APIRouter(prefix="/api/collections", tags=["collections"])


def _row_to_response(row: sqlite3.Row, bookmark_count: int) -> CollectionResponse:
    return CollectionResponse(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        color=row["color"],
        bookmark_count=bookmark_count,
        created_at=row["created_at"],
    )


@router.post("", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
def create_collection(payload: CollectionCreate) -> CollectionResponse:
    collection_id = uuid.uuid4().hex
    with get_db() as db:
        try:
            db.execute(
                "INSERT INTO collections(id, name, description, color) "
                "VALUES (?, ?, ?, ?)",
                (collection_id, payload.name, payload.description, payload.color),
            )
        except sqlite3.IntegrityError as exc:
            raise HTTPException(status_code=409, detail="collection name already exists") from exc
        row = db.execute(
            "SELECT * FROM collections WHERE id = ?", (collection_id,)
        ).fetchone()
    return _row_to_response(row, 0)


@router.get("", response_model=list[CollectionResponse])
def list_collections() -> list[CollectionResponse]:
    with get_db() as db:
        rows = db.execute(
            "SELECT c.*, "
            "(SELECT COUNT(*) FROM bookmarks b WHERE b.collection_id = c.id) AS bookmark_count "
            "FROM collections c ORDER BY c.name"
        ).fetchall()
    return [_row_to_response(r, r["bookmark_count"]) for r in rows]


@router.get("/{collection_id}", response_model=CollectionResponse)
def get_collection(collection_id: str) -> CollectionResponse:
    with get_db() as db:
        row = db.execute(
            "SELECT c.*, "
            "(SELECT COUNT(*) FROM bookmarks b WHERE b.collection_id = c.id) AS bookmark_count "
            "FROM collections c WHERE c.id = ?",
            (collection_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="collection not found")
    return _row_to_response(row, row["bookmark_count"])


@router.put("/{collection_id}", response_model=CollectionResponse)
def update_collection(collection_id: str, payload: CollectionUpdate) -> CollectionResponse:
    data = payload.model_dump(exclude_unset=True)
    with get_db() as db:
        existing = db.execute(
            "SELECT 1 FROM collections WHERE id = ?", (collection_id,)
        ).fetchone()
        if existing is None:
            raise HTTPException(status_code=404, detail="collection not found")

        set_parts: list[str] = []
        values: list[Any] = []
        for field in ("name", "description", "color"):
            if field in data:
                set_parts.append(f"{field} = ?")
                values.append(data[field])

        if set_parts:
            values.append(collection_id)
            try:
                db.execute(
                    f"UPDATE collections SET {', '.join(set_parts)} WHERE id = ?",
                    values,
                )
            except sqlite3.IntegrityError as exc:
                raise HTTPException(status_code=409, detail="collection name already exists") from exc

        row = db.execute(
            "SELECT c.*, "
            "(SELECT COUNT(*) FROM bookmarks b WHERE b.collection_id = c.id) AS bookmark_count "
            "FROM collections c WHERE c.id = ?",
            (collection_id,),
        ).fetchone()
    return _row_to_response(row, row["bookmark_count"])


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_collection(collection_id: str) -> Response:
    with get_db() as db:
        existing = db.execute(
            "SELECT 1 FROM collections WHERE id = ?", (collection_id,)
        ).fetchone()
        if existing is None:
            raise HTTPException(status_code=404, detail="collection not found")
        db.execute("DELETE FROM collections WHERE id = ?", (collection_id,))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
