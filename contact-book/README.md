# Contact Book

## Overview

Contact Book is a REST API for managing personal contacts, built with FastAPI, Pydantic v2, and SQLite. It provides CRUD operations plus name-based search, and creates its SQLite schema automatically at startup via `init_db()`.

## Project Layout

```
contact-book/
├── contacts/
│   ├── __init__.py
│   ├── db.py          — SQLite connection, schema, init_db
│   ├── models.py      — Pydantic models: Contact, ContactCreate, ContactUpdate
│   ├── repository.py  — CRUD functions: create, get_by_id, list_all, update, delete, search_by_name
│   ├── api.py         — FastAPI router for /contacts endpoints
│   └── main.py        — FastAPI app with lifespan (calls init_db on startup)
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_db.py
    ├── test_models.py
    ├── test_repository.py
    └── test_api.py
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set the required environment variable before running the app or tests:

```bash
export DATABASE_URL=sqlite:///data/contacts.db
```

> **Note:** `DATABASE_URL` is required. The application raises a `RuntimeError` at startup if it is not set.

## Running the API

```bash
uvicorn contacts.main:app --reload
```

The FastAPI lifespan hook calls `init_db()` on startup, creating the `contacts` table and name index if they do not already exist.

## API Endpoints

| Method | Path | Description | Status Codes |
|--------|------|-------------|--------------|
| `POST` | `/contacts` | Create a new contact | 201 Created |
| `GET` | `/contacts` | List all contacts (sorted by name) | 200 OK |
| `GET` | `/contacts/{id}` | Get a contact by ID | 200 OK, 404 Not Found |
| `PUT` | `/contacts/{id}` | Update a contact | 200 OK, 404 Not Found |
| `DELETE` | `/contacts/{id}` | Delete a contact | 204 No Content, 404 Not Found |
| `GET` | `/contacts/search?q=...` | Search contacts by name (case-insensitive substring) | 200 OK, 422 Unprocessable Entity (if `q` is missing), 200 OK with `[]` (if `q` is empty) |

Interactive API docs are available at `http://127.0.0.1:8000/docs` when the server is running.

## Import / Export

This branch does not include import or export utilities. There is no `contacts/export.py` module or related test coverage in the current codebase, so import/export usage is intentionally not documented here.

## Running Tests

From the `contact-book/` directory:

```bash
pytest
```
