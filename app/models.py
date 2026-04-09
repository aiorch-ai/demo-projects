"""Pydantic v2 models for the Invoice Management API."""

import secrets
import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# --- Tenant Models ---

class TenantCreate(BaseModel):
    model_config = ConfigDict(strict=False)

    name: str
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    api_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))


class TenantResponse(BaseModel):
    model_config = ConfigDict(strict=False)

    id: str
    name: str
    is_active: bool
    created_at: str
    updated_at: str


# --- Client Models ---

class ClientCreate(BaseModel):
    model_config = ConfigDict(strict=False)

    name: str
    email: str | None = None
    address: str | None = None
    phone: str | None = None


class ClientResponse(BaseModel):
    model_config = ConfigDict(strict=False)

    id: str
    tenant_id: str
    name: str
    email: str | None
    address: str | None
    phone: str | None
    created_at: str
    updated_at: str


# --- Line Item Models ---

class LineItemCreate(BaseModel):
    model_config = ConfigDict(strict=False)

    description: str
    quantity: float = 1.0
    unit_price: float


class LineItemResponse(BaseModel):
    model_config = ConfigDict(strict=False)

    id: str
    invoice_id: str
    description: str
    quantity: float
    unit_price: float
    amount: float
    sort_order: int
    created_at: str


# --- Invoice Models ---

class InvoiceCreate(BaseModel):
    model_config = ConfigDict(strict=False)

    client_id: str
    issue_date: str
    due_date: str
    tax_rate: float = 0.0
    notes: str | None = None
    line_items: list[LineItemCreate]


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(strict=False)

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
    model_config = ConfigDict(strict=False)

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
    model_config = ConfigDict(strict=False)

    status: Literal["draft", "sent", "paid", "overdue", "cancelled"]
