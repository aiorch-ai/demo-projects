"""FastAPI application entry point for the Weather Dashboard API."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import database
from app.database import get_db, init_db
from app.routes import cities, weather
from app.seed import seed_demo_data


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    with get_db() as db:
        row = db.execute("SELECT COUNT(*) AS c FROM cities").fetchone()
    if row["c"] == 0:
        db_path = database._db_path_from_url(os.environ["DATABASE_URL"])
        seed_demo_data(db_path)
    yield


app = FastAPI(title="Weather Dashboard API", version="1.0.0", lifespan=lifespan)

app.include_router(cities.router)
app.include_router(weather.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "1.0.0"}
