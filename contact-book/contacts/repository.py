from __future__ import annotations

import uuid
from sqlite3 import Connection

from contacts.db import get_db
from contacts.models import Contact, ContactCreate, ContactUpdate


def _row_to_contact(row) -> Contact:
    return Contact(
        id=row["id"],
        name=row["name"],
        email=row["email"],
        phone=row["phone"],
        company=row["company"],
        notes=row["notes"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def create(data: ContactCreate) -> Contact:
    contact_id = uuid.uuid4().hex
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO contacts (id, name, email, phone, company, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                contact_id,
                data.name,
                data.email,
                data.phone,
                data.company,
                data.notes,
            ),
        )
        return _get_by_id_from_conn(conn, contact_id)


def get_by_id(contact_id: str) -> Contact | None:
    with get_db() as conn:
        return _get_by_id_from_conn(conn, contact_id)


def _get_by_id_from_conn(conn: Connection, contact_id: str) -> Contact | None:
    cur = conn.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,))
    row = cur.fetchone()
    if row is None:
        return None
    return _row_to_contact(row)


def list_all() -> list[Contact]:
    with get_db() as conn:
        cur = conn.execute("SELECT * FROM contacts ORDER BY name ASC")
        return [_row_to_contact(row) for row in cur.fetchall()]


def update(contact_id: str, data: ContactUpdate) -> Contact | None:
    fields = data.model_dump(exclude_unset=True)
    if not fields:
        with get_db() as conn:
            conn.execute(
                "UPDATE contacts SET updated_at = datetime('now') WHERE id = ?",
                (contact_id,),
            )
            if conn.total_changes == 0:
                return None
            return _get_by_id_from_conn(conn, contact_id)

    set_clause = ", ".join(f"{key} = ?" for key in fields)
    values = list(fields.values())
    values.append(contact_id)

    with get_db() as conn:
        cur = conn.execute(
            f"UPDATE contacts SET {set_clause}, updated_at = datetime('now') WHERE id = ?",
            values,
        )
        if cur.rowcount == 0:
            return None
        return _get_by_id_from_conn(conn, contact_id)


def delete(contact_id: str) -> bool:
    with get_db() as conn:
        cur = conn.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
        return cur.rowcount > 0


def search_by_name(query: str) -> list[Contact]:
    if not query:
        return []
    pattern = f"%{query}%"
    with get_db() as conn:
        cur = conn.execute(
            "SELECT * FROM contacts WHERE name LIKE ? COLLATE NOCASE ORDER BY name ASC",
            (pattern,),
        )
        return [_row_to_contact(row) for row in cur.fetchall()]
