"""FastAPI application entry point for the Bookmark Manager API."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import database
from app.database import get_db, init_db
from app.routes import bookmarks, collections, import_export, search, tags
from app.seed import seed_demo_data


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    with get_db() as db:
        row = db.execute("SELECT COUNT(*) AS c FROM bookmarks").fetchone()
    if row["c"] == 0:
        db_path = database._db_path_from_url(os.environ["DATABASE_URL"])
        seed_demo_data(db_path)
    yield


app = FastAPI(title="Bookmark Manager API", version="1.0.0", lifespan=lifespan)


app.include_router(search.router)
app.include_router(import_export.router)
app.include_router(bookmarks.router)
app.include_router(collections.router)
app.include_router(tags.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "1.0.0"}
