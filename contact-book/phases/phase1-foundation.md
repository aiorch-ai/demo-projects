Build the data layer for a contact book application inside `contact-book/`.

Create:
- `contact-book/contacts/db.py` — SQLite connection and schema (contacts table: id, name, email, phone, company, notes, created_at, updated_at)
- `contact-book/contacts/models.py` — Pydantic models: Contact, ContactCreate, ContactUpdate
- `contact-book/contacts/repository.py` — CRUD: create, get_by_id, list_all, update, delete, search_by_name
- `contact-book/contacts/__init__.py`
- `contact-book/tests/test_repository.py` — Tests for all repository operations
- `contact-book/requirements.txt` — pydantic, pytest
