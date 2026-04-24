from __future__ import annotations

import csv
import io
import json

import pytest

from contacts.export import CSV_FIELDS, export_to_csv, export_to_json, import_from_csv
from contacts.models import ContactCreate
from contacts.repository import create, delete, list_all


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------


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

    out = io.StringIO()
    count = export_to_csv(out)
    assert count == 2

    out.seek(0)
    rows = list(csv.DictReader(out))
    assert len(rows) == 2
    assert rows[0]["name"] == "Alice"
    assert rows[0]["email"] == "alice@example.com"
    assert rows[1]["name"] == "Bob"
    assert rows[1]["phone"] == "555-1234"
    # Optional empty fields are present but empty in CSV
    assert rows[1]["email"] == ""


# ---------------------------------------------------------------------------
# JSON export
# ---------------------------------------------------------------------------


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
    # All Contact fields are present
    for field in CSV_FIELDS:
        assert field in data[0]


# ---------------------------------------------------------------------------
# CSV import
# ---------------------------------------------------------------------------


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


def test_import_empty_fields_become_none(db):
    csv_text = "name,email,phone,company,notes\n" "Charlie,,,,\n"
    fp = io.StringIO(csv_text)
    imported = import_from_csv(fp)
    assert len(imported) == 1
    contact = imported[0]
    assert contact.name == "Charlie"
    assert contact.email is None
    assert contact.phone is None
    assert contact.company is None
    assert contact.notes is None


def test_import_ignores_extra_columns(db):
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


def test_import_skips_blank_rows(db):
    csv_text = (
        "name,email\n"
        "Alice,alice@example.com\n"
        ",\n"
        "   ,   \n"
        "Bob,bob@example.com\n"
    )
    fp = io.StringIO(csv_text)
    imported = import_from_csv(fp)
    assert len(imported) == 2
    assert {c.name for c in imported} == {"Alice", "Bob"}


def test_import_raises_on_missing_name(db):
    csv_text = "name,email\n,alice@example.com\n"
    fp = io.StringIO(csv_text)
    with pytest.raises(ValueError, match="missing required 'name'"):
        import_from_csv(fp)


def test_import_raises_when_name_column_absent(db):
    csv_text = "email,phone\nalice@example.com,555-1234\n"
    fp = io.StringIO(csv_text)
    with pytest.raises(ValueError, match="missing required 'name'"):
        import_from_csv(fp)


# ---------------------------------------------------------------------------
# Round-trip & edge cases
# ---------------------------------------------------------------------------


def test_round_trip_csv(db):
    """Export then re-import; content (not IDs) must survive."""
    original = [
        create(ContactCreate(name="Alice", email="alice@example.com")),
        create(ContactCreate(name="Bob", phone="555-1234", company="Acme")),
    ]

    out = io.StringIO()
    export_to_csv(out)

    # Remove original contacts so re-import is clean
    for contact in original:
        delete(contact.id)
    assert list_all() == []

    out.seek(0)
    imported = import_from_csv(out)
    assert len(imported) == 2

    assert imported[0].name == original[0].name
    assert imported[0].email == original[0].email
    assert imported[1].name == original[1].name
    assert imported[1].phone == original[1].phone
    assert imported[1].company == original[1].company


def test_csv_handles_quoted_fields(db):
    """Names and notes with commas, quotes, and newlines survive round-trip."""
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
