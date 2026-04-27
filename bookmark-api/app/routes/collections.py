"""Collection CRUD endpoints under /api/collections."""

import sqlite3
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.database import get_db
from app.models import CollectionCreate, CollectionResponse

router = APIRouter(prefix="/api/collections", tags=["collections"])


class CollectionUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    color: str | None = None


def _row_to_response(row: sqlite3.Row, bookmark_count: int) -> CollectionResponse:
    return CollectionResponse(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        color=row["color"],
        bookmark_count=bookmark_count,
        created_at=row["created_at"],
    )


def _count_bookmarks(db: sqlite3.Connection, collection_id: str) -> int:
    row = db.execute(
        "SELECT COUNT(*) AS c FROM bookmarks WHERE collection_id = ?",
        (collection_id,),
    ).fetchone()
    return int(row["c"])


@router.post("", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
def create_collection(
    payload: CollectionCreate,
    db: sqlite3.Connection = Depends(get_db),
) -> CollectionResponse:
    collection_id = str(uuid4())
    try:
        db.execute(
            """
            INSERT INTO collections (id, name, description, color)
            VALUES (?, ?, ?, ?)
            """,
            (collection_id, payload.name, payload.description, payload.color),
        )
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail=f"Collection with name '{payload.name}' already exists",
        ) from exc
    row = db.execute(
        "SELECT * FROM collections WHERE id = ?", (collection_id,)
    ).fetchone()
    return _row_to_response(row, 0)


@router.get("", response_model=list[CollectionResponse])
def list_collections(
    db: sqlite3.Connection = Depends(get_db),
) -> list[CollectionResponse]:
    rows = db.execute(
        """
        SELECT c.id, c.name, c.description, c.color, c.created_at,
               COUNT(b.id) AS bookmark_count
          FROM collections c
          LEFT JOIN bookmarks b ON b.collection_id = c.id
         GROUP BY c.id
         ORDER BY c.name
        """
    ).fetchall()
    return [
        CollectionResponse(
            id=r["id"],
            name=r["name"],
            description=r["description"],
            color=r["color"],
            bookmark_count=int(r["bookmark_count"]),
            created_at=r["created_at"],
        )
        for r in rows
    ]


@router.get("/{collection_id}", response_model=CollectionResponse)
def get_collection(
    collection_id: str,
    db: sqlite3.Connection = Depends(get_db),
) -> CollectionResponse:
    row = db.execute(
        "SELECT * FROM collections WHERE id = ?", (collection_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Collection not found")
    return _row_to_response(row, _count_bookmarks(db, collection_id))


@router.put("/{collection_id}", response_model=CollectionResponse)
def update_collection(
    collection_id: str,
    payload: CollectionUpdate,
    db: sqlite3.Connection = Depends(get_db),
) -> CollectionResponse:
    existing = db.execute(
        "SELECT id FROM collections WHERE id = ?", (collection_id,)
    ).fetchone()
    if existing is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    data = payload.model_dump(exclude_unset=True)
    if data:
        set_parts = [f"{field} = ?" for field in data]
        set_parts.append("updated_at = datetime('now')")
        values = list(data.values()) + [collection_id]
        try:
            db.execute(
                f"UPDATE collections SET {', '.join(set_parts)} WHERE id = ?",
                tuple(values),
            )
        except sqlite3.IntegrityError as exc:
            raise HTTPException(
                status_code=409,
                detail="Collection with this name already exists",
            ) from exc

    row = db.execute(
        "SELECT * FROM collections WHERE id = ?", (collection_id,)
    ).fetchone()
    return _row_to_response(row, _count_bookmarks(db, collection_id))


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_collection(
    collection_id: str,
    db: sqlite3.Connection = Depends(get_db),
) -> None:
    cursor = db.execute(
        "DELETE FROM collections WHERE id = ?", (collection_id,)
    )
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Collection not found")
