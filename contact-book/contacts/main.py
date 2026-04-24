from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from contacts.api import router
from contacts.db import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Contact Book API", version="1.0.0", lifespan=lifespan)

app.include_router(router)
