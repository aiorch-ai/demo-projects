"""FastAPI application entry point for the Snippet Vault API."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import database
from app.database import get_db, init_db
from app.routes import snippets, stats, tags
from app.seed import seed_demo_data


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    with get_db() as db:
        row = db.execute("SELECT COUNT(*) AS c FROM snippets").fetchone()
    if row["c"] == 0:
        db_path = database._db_path_from_url(os.environ["DATABASE_URL"])
        seed_demo_data(db_path)
    yield


app = FastAPI(title="Snippet Vault API", version="1.0.0", lifespan=lifespan)

app.include_router(snippets.router)
app.include_router(tags.router)
app.include_router(stats.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "1.0.0"}
