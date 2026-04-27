"""FastAPI application entrypoint for the Bookmark Manager API."""

import os
import sqlite3
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db
from app.seed import seed_demo_data


def _db_path_from_url() -> str:
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL environment variable is not set or empty")
    return db_url.replace("sqlite:///", "", 1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db_path = _db_path_from_url()
    conn = sqlite3.connect(db_path)
    try:
        count = conn.execute("SELECT COUNT(*) FROM bookmarks").fetchone()[0]
    finally:
        conn.close()
    if count == 0:
        seed_demo_data(db_path)
    yield


app = FastAPI(
    title="Bookmark Manager API",
    version="1.0.0",
    lifespan=lifespan,
)


# Register routers in a specific order: search and import_export must be
# included BEFORE the bookmarks router so that /api/bookmarks/search and
# /api/bookmarks/export are matched before the dynamic /api/bookmarks/{id}.
# search.py and import_export.py are owned by agent-3; tolerate their absence
# during incremental development.
try:
    from app.routes import search as search_routes

    app.include_router(search_routes.router)
except ImportError:
    pass

try:
    from app.routes import import_export as import_export_routes

    app.include_router(import_export_routes.router)
except ImportError:
    pass

from app.routes import bookmarks, collections, tags  # noqa: E402

app.include_router(bookmarks.router)
app.include_router(collections.router)
app.include_router(tags.router)


@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}
