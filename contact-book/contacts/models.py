from __future__ import annotations

from pydantic import BaseModel


class ContactCreate(BaseModel):
    name: str
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    notes: str | None = None


class ContactUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    notes: str | None = None


class Contact(BaseModel):
    id: str
    name: str
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    notes: str | None = None
    created_at: str
    updated_at: str
