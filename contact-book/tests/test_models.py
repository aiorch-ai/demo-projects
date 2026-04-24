from __future__ import annotations

import pytest
from pydantic import ValidationError

from contacts.models import Contact, ContactCreate, ContactUpdate


def test_contact_create_required_name():
    with pytest.raises(ValidationError):
        ContactCreate()


def test_contact_create_with_all_fields():
    cc = ContactCreate(
        name="Alice",
        email="alice@example.com",
        phone="555-1234",
        company="Example Inc",
        notes="A note",
    )
    assert cc.name == "Alice"
    assert cc.email == "alice@example.com"
    assert cc.phone == "555-1234"
    assert cc.company == "Example Inc"
    assert cc.notes == "A note"


def test_contact_create_defaults():
    cc = ContactCreate(name="Bob")
    assert cc.name == "Bob"
    assert cc.email is None
    assert cc.phone is None
    assert cc.company is None
    assert cc.notes is None


def test_contact_update_all_optional():
    cu = ContactUpdate()
    assert cu.name is None
    assert cu.email is None
    assert cu.phone is None
    assert cu.company is None
    assert cu.notes is None


def test_contact_update_partial():
    cu = ContactUpdate(name="New Name")
    assert cu.name == "New Name"
    assert cu.email is None


def test_contact_model():
    c = Contact(
        id="abc123",
        name="Charlie",
        email="charlie@example.com",
        phone="555-5678",
        company="Acme",
        notes="Some notes",
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-02T00:00:00",
    )
    assert c.id == "abc123"
    assert c.name == "Charlie"
    assert c.email == "charlie@example.com"
    assert c.phone == "555-5678"
    assert c.company == "Acme"
    assert c.notes == "Some notes"
    assert c.created_at == "2024-01-01T00:00:00"
    assert c.updated_at == "2024-01-02T00:00:00"


def test_contact_model_optional_fields_default_none():
    c = Contact(
        id="xyz",
        name="Dana",
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00",
    )
    assert c.email is None
    assert c.phone is None
    assert c.company is None
    assert c.notes is None


def test_contact_model_serialization():
    c = Contact(
        id="id1",
        name="Eve",
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00",
    )
    data = c.model_dump()
    assert data["id"] == "id1"
    assert data["name"] == "Eve"
    assert data["email"] is None
    assert data["created_at"] == "2024-01-01T00:00:00"
