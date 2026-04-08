"""Tests for Pydantic v2 models."""

import uuid

import pytest
from pydantic import ValidationError

from app.models import (
    ClientCreate,
    ClientResponse,
    InvoiceCreate,
    InvoiceListResponse,
    InvoiceResponse,
    InvoiceStatusUpdate,
    LineItemCreate,
    LineItemResponse,
    TenantCreate,
    TenantResponse,
)


class TestTenantCreate:
    def test_auto_generates_id(self):
        tenant = TenantCreate(name="Acme Corp")
        assert tenant.id is not None
        # Verify it's a valid UUID
        uuid.UUID(tenant.id)

    def test_auto_generates_api_key(self):
        tenant = TenantCreate(name="Acme Corp")
        assert tenant.api_key is not None
        assert len(tenant.api_key) > 0

    def test_unique_ids_and_keys(self):
        t1 = TenantCreate(name="A")
        t2 = TenantCreate(name="B")
        assert t1.id != t2.id
        assert t1.api_key != t2.api_key

    def test_name_required(self):
        with pytest.raises(ValidationError):
            TenantCreate()


class TestTenantResponse:
    def test_excludes_api_key(self):
        data = {
            "id": "123",
            "name": "Acme",
            "is_active": True,
            "created_at": "2024-01-01",
            "updated_at": "2024-01-01",
        }
        tenant = TenantResponse(**data)
        assert not hasattr(tenant, "api_key")
        fields = set(TenantResponse.model_fields.keys())
        assert "api_key" not in fields

    def test_all_fields_required(self):
        with pytest.raises(ValidationError):
            TenantResponse(id="123", name="Acme")


class TestClientCreate:
    def test_name_required(self):
        with pytest.raises(ValidationError):
            ClientCreate()

    def test_optional_fields_accept_none(self):
        client = ClientCreate(name="John")
        assert client.email is None
        assert client.address is None
        assert client.phone is None

    def test_optional_fields_accept_values(self):
        client = ClientCreate(
            name="John",
            email="john@example.com",
            address="123 Main St",
            phone="555-1234",
        )
        assert client.email == "john@example.com"
        assert client.address == "123 Main St"
        assert client.phone == "555-1234"


class TestClientResponse:
    def test_all_fields_required(self):
        with pytest.raises(ValidationError):
            ClientResponse(id="1", name="John")

    def test_valid_response(self):
        resp = ClientResponse(
            id="1",
            tenant_id="t1",
            name="John",
            email=None,
            address=None,
            phone=None,
            created_at="2024-01-01",
            updated_at="2024-01-01",
        )
        assert resp.tenant_id == "t1"


class TestLineItemCreate:
    def test_defaults_quantity_to_one(self):
        item = LineItemCreate(description="Widget", unit_price=10.0)
        assert item.quantity == 1.0

    def test_description_required(self):
        with pytest.raises(ValidationError):
            LineItemCreate(unit_price=10.0)

    def test_unit_price_required(self):
        with pytest.raises(ValidationError):
            LineItemCreate(description="Widget")


class TestLineItemResponse:
    def test_all_fields_required(self):
        with pytest.raises(ValidationError):
            LineItemResponse(id="1", description="Widget")

    def test_valid_response(self):
        resp = LineItemResponse(
            id="1",
            invoice_id="inv1",
            description="Widget",
            quantity=2.0,
            unit_price=10.0,
            amount=20.0,
            sort_order=0,
            created_at="2024-01-01",
        )
        assert resp.amount == 20.0


class TestInvoiceCreate:
    def test_accepts_nested_line_items(self):
        invoice = InvoiceCreate(
            client_id="c1",
            issue_date="2024-01-01",
            due_date="2024-02-01",
            line_items=[
                LineItemCreate(description="Widget A", unit_price=10.0),
                LineItemCreate(description="Widget B", quantity=3, unit_price=5.0),
            ],
        )
        assert len(invoice.line_items) == 2
        assert invoice.line_items[0].quantity == 1.0
        assert invoice.line_items[1].quantity == 3.0

    def test_tax_rate_defaults_to_zero(self):
        invoice = InvoiceCreate(
            client_id="c1",
            issue_date="2024-01-01",
            due_date="2024-02-01",
            line_items=[LineItemCreate(description="X", unit_price=1.0)],
        )
        assert invoice.tax_rate == 0.0

    def test_notes_optional(self):
        invoice = InvoiceCreate(
            client_id="c1",
            issue_date="2024-01-01",
            due_date="2024-02-01",
            line_items=[LineItemCreate(description="X", unit_price=1.0)],
        )
        assert invoice.notes is None

    def test_client_id_required(self):
        with pytest.raises(ValidationError):
            InvoiceCreate(
                issue_date="2024-01-01",
                due_date="2024-02-01",
                line_items=[],
            )


class TestInvoiceResponse:
    def test_includes_line_items(self):
        resp = InvoiceResponse(
            id="inv1",
            tenant_id="t1",
            client_id="c1",
            invoice_number="INV-001",
            status="draft",
            issue_date="2024-01-01",
            due_date="2024-02-01",
            subtotal=100.0,
            tax_rate=0.1,
            tax_amount=10.0,
            total=110.0,
            notes=None,
            line_items=[
                LineItemResponse(
                    id="li1",
                    invoice_id="inv1",
                    description="Widget",
                    quantity=1.0,
                    unit_price=100.0,
                    amount=100.0,
                    sort_order=0,
                    created_at="2024-01-01",
                ),
            ],
            created_at="2024-01-01",
            updated_at="2024-01-01",
        )
        assert len(resp.line_items) == 1


class TestInvoiceListResponse:
    def test_no_line_items_field(self):
        fields = set(InvoiceListResponse.model_fields.keys())
        assert "line_items" not in fields

    def test_valid_response(self):
        resp = InvoiceListResponse(
            id="inv1",
            tenant_id="t1",
            client_id="c1",
            invoice_number="INV-001",
            status="draft",
            issue_date="2024-01-01",
            due_date="2024-02-01",
            subtotal=100.0,
            tax_rate=0.1,
            tax_amount=10.0,
            total=110.0,
            notes=None,
            created_at="2024-01-01",
            updated_at="2024-01-01",
        )
        assert resp.invoice_number == "INV-001"

    def test_does_not_inherit_from_invoice_response(self):
        assert not issubclass(InvoiceListResponse, InvoiceResponse)


class TestInvoiceStatusUpdate:
    def test_valid_statuses(self):
        for status in ["draft", "sent", "paid", "overdue", "cancelled"]:
            update = InvoiceStatusUpdate(status=status)
            assert update.status == status

    def test_rejects_invalid_status(self):
        with pytest.raises(ValidationError):
            InvoiceStatusUpdate(status="invalid")

    def test_rejects_empty_status(self):
        with pytest.raises(ValidationError):
            InvoiceStatusUpdate(status="")

    def test_status_required(self):
        with pytest.raises(ValidationError):
            InvoiceStatusUpdate()
