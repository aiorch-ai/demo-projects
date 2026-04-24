from __future__ import annotations

import csv
import io
import json

import pytest
from pydantic import ValidationError

from contacts.export import CSV_FIELDS, export_to_csv, export_to_json, import_from_csv
from contacts.models import ContactCreate
from contacts.repository import create, delete, list_all


def test_export_csv_empty(db):
    out = io.StringIO()
    count = export_to_csv(out)
    assert count == 0
    out.seek(0)
    reader = csv.DictReader(out)
    assert reader.fieldnames == list(CSV_FIELDS)
    assert list(reader) == []


def test_export_csv_with_rows(db):
    create(ContactCreate(name="Alice", email="alice@example.com"))
    create(ContactCreate(name="Bob", phone="555-1234"))
    create(ContactCreate(name="Charlie", company="Acme", notes="A note"))

    out = io.StringIO()
    count = export_to_csv(out)
    assert count == 3

    out.seek(0)
    reader = csv.DictReader(out)
    assert reader.fieldnames == list(CSV_FIELDS)
    rows = list(reader)
    assert len(rows) == 3
    assert rows[0]["name"] == "Alice"
    assert rows[0]["email"] == "alice@example.com"
    assert rows[1]["name"] == "Bob"
    assert rows[1]["phone"] == "555-1234"
    assert rows[2]["name"] == "Charlie"
    assert rows[2]["company"] == "Acme"
    assert rows[2]["notes"] == "A note"


def test_export_json_empty(db):
    out = io.StringIO()
    count = export_to_json(out)
    assert count == 0
    out.seek(0)
    data = json.load(out)
    assert data == []


def test_export_json_with_rows(db):
    create(ContactCreate(name="Alice"))
    create(ContactCreate(name="Bob", notes="A note"))

    out = io.StringIO()
    count = export_to_json(out)
    assert count == 2

    out.seek(0)
    data = json.load(out)
    assert len(data) == 2
    assert data[0]["name"] == "Alice"
    assert data[0]["email"] is None
    assert data[1]["name"] == "Bob"
    assert data[1]["notes"] == "A note"
    # All Contact fields are present in each dict
    for field in CSV_FIELDS:
        assert field in data[0]
        assert field in data[1]


def test_import_from_csv_basic(db):
    csv_text = (
        "name,email,phone\n"
        "Alice,alice@example.com,555-1111\n"
        "Bob,bob@example.com,555-2222\n"
    )
    fp = io.StringIO(csv_text)
    imported = import_from_csv(fp)
    assert len(imported) == 2
    assert imported[0].name == "Alice"
    assert imported[1].name == "Bob"

    all_contacts = list_all()
    assert len(all_contacts) == 2
    assert all_contacts[0].name == "Alice"
    assert all_contacts[0].email == "alice@example.com"
    assert all_contacts[1].name == "Bob"
    assert all_contacts[1].email == "bob@example.com"


def test_import_empty_fields_become_none(db):
    csv_text = "name,email,phone,company,notes\nCharlie,,,,\n"
    fp = io.StringIO(csv_text)
    imported = import_from_csv(fp)
    assert len(imported) == 1
    contact = imported[0]
    assert contact.name == "Charlie"
    assert contact.email is None
    assert contact.phone is None
    assert contact.company is None
    assert contact.notes is None


def test_import_ignores_id_and_timestamps(db):
    csv_text = (
        "id,name,email,created_at,updated_at\n"
        "old-id-123,Dana,dana@example.com,2020-01-01,2020-01-02\n"
    )
    fp = io.StringIO(csv_text)
    imported = import_from_csv(fp)
    assert len(imported) == 1
    assert imported[0].name == "Dana"
    assert imported[0].email == "dana@example.com"
    # DB generates fresh id and timestamps; old values are ignored
    assert imported[0].id != "old-id-123"
    assert imported[0].created_at != "2020-01-01"


def test_import_missing_name_raises(db):
    csv_text = "name,email\n,alice@example.com\n"
    fp = io.StringIO(csv_text)
    with pytest.raises((ValueError, ValidationError)):
        import_from_csv(fp)


def test_round_trip_csv(db):
    original = [
        create(ContactCreate(name="Alice", email="alice@example.com")),
        create(ContactCreate(name="Bob", phone="555-1234", company="Acme")),
    ]

    out = io.StringIO()
    export_to_csv(out)

    # Clear the database so re-import is clean
    for contact in original:
        delete(contact.id)
    assert list_all() == []

    out.seek(0)
    imported = import_from_csv(out)
    assert len(imported) == 2

    for orig, imp in zip(original, imported):
        assert imp.name == orig.name
        assert imp.email == orig.email
        assert imp.phone == orig.phone
        assert imp.company == orig.company
        assert imp.notes == orig.notes


def test_csv_handles_quoted_fields(db):
    create(
        ContactCreate(
            name='Doe, John',
            notes='He said "Hello"\nThen left.',
        )
    )

    out = io.StringIO()
    export_to_csv(out)
    out.seek(0)

    imported = import_from_csv(out)
    assert len(imported) == 1
    assert imported[0].name == "Doe, John"
    assert imported[0].notes == 'He said "Hello"\nThen left.'
