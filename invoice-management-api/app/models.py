"""Pydantic models for the invoice management API.

These models are intentionally aligned with the SQLite schema in app/schema.py.
SQLite stores timestamps/dates as TEXT, so date/time fields are represented as str.

Note: sqlite3.Row is dict-like (row["col"]) rather than attribute-based, so
callers should typically use `Model.model_validate(dict(row))`.
"""

from __future__ import annotations

import secrets
from typing import ClassVar
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TenantCreate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    api_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))


class TenantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    is_active: bool
    created_at: str
    updated_at: str


class ClientCreate(BaseModel):
    name: str
    email: str | None = None
    address: str | None = None
    phone: str | None = None


class ClientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    name: str
    email: str | None
    address: str | None
    phone: str | None
    created_at: str
    updated_at: str


class LineItemCreate(BaseModel):
    description: str
    quantity: float
    unit_price: float

    @field_validator("quantity")
    @classmethod
    def _quantity_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("quantity must be >= 0")
        return v

    @field_validator("unit_price")
    @classmethod
    def _unit_price_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("unit_price must be >= 0")
        return v


class LineItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    invoice_id: str
    description: str
    quantity: float
    unit_price: float
    amount: float
    sort_order: int
    created_at: str


class InvoiceCreate(BaseModel):
    client_id: str
    issue_date: str
    due_date: str
    tax_rate: float = 0.0
    notes: str | None = None
    line_items: list[LineItemCreate]


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    client_id: str
    invoice_number: str
    status: str
    issue_date: str
    due_date: str
    subtotal: float
    tax_rate: float
    tax_amount: float
    total: float
    notes: str | None
    line_items: list[LineItemResponse]
    created_at: str
    updated_at: str


class InvoiceListResponse(BaseModel):
    """Invoice response for list endpoints (no line_items)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    client_id: str
    invoice_number: str
    status: str
    issue_date: str
    due_date: str
    subtotal: float
    tax_rate: float
    tax_amount: float
    total: float
    notes: str | None
    created_at: str
    updated_at: str


class InvoiceStatusUpdate(BaseModel):
    status: str

    VALID_TRANSITIONS: ClassVar[dict[str, list[str]]] = {
        "draft": ["sent", "cancelled"],
        "sent": ["paid", "overdue", "cancelled"],
        "overdue": ["paid", "cancelled"],
        "paid": [],
        "cancelled": [],
    }

    @classmethod
    def is_valid_transition(cls, current: str, new: str) -> bool:
        return new in cls.VALID_TRANSITIONS.get(current, [])

    @field_validator("status")
    @classmethod
    def _status_known(cls, v: str) -> str:
        if v not in cls.VALID_TRANSITIONS:
            raise ValueError(
                f"invalid status '{v}'; must be one of: {', '.join(cls.VALID_TRANSITIONS.keys())}"
            )
        return v
