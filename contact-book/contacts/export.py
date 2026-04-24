from __future__ import annotations

import csv
import json
from typing import IO

from contacts.models import Contact, ContactCreate
from contacts.repository import create, list_all

CSV_FIELDS = (
    "id",
    "name",
    "email",
    "phone",
    "company",
    "notes",
    "created_at",
    "updated_at",
)

_CONTACT_CREATE_FIELDS = {"name", "email", "phone", "company", "notes"}


def export_to_csv(fp: IO[str]) -> int:
    """Export all contacts to *fp* as CSV. Returns the number of rows written."""
    writer = csv.DictWriter(fp, fieldnames=CSV_FIELDS, quoting=csv.QUOTE_MINIMAL)
    writer.writeheader()
    count = 0
    for contact in list_all():
        writer.writerow(contact.model_dump())
        count += 1
    return count


def export_to_json(fp: IO[str]) -> int:
    """Export all contacts to *fp* as JSON. Returns the number of rows written."""
    contacts = list_all()
    json.dump([c.model_dump() for c in contacts], fp, indent=2)
    return len(contacts)


def import_from_csv(fp: IO[str]) -> list[Contact]:
    """Import contacts from a CSV file-like object.

    Each row is validated, optional empty cells are coerced to ``None``,
    and extraneous columns (such as ``id`` or timestamps from a previous export)
    are ignored. A :exc:`ValueError` is raised if ``name`` is missing or empty.
    """
    reader = csv.DictReader(fp)
    created: list[Contact] = []

    for row in reader:
        # Skip fully-blank rows
        if not row or all(v.strip() == "" for v in row.values()):
            continue

        # Drop keys not in ContactCreate fields
        clean_row: dict[str, str | None] = {}
        for key in _CONTACT_CREATE_FIELDS:
            value = row.get(key, "")
            if value is not None and value.strip() == "":
                value = None
            clean_row[key] = value

        name = clean_row.get("name")
        if name is None or name.strip() == "":
            raise ValueError("CSV row missing required 'name' field")

        created.append(create(ContactCreate(**clean_row)))

    return created
