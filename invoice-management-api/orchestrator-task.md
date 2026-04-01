# AiOrch Session Task — Invoice Management API

This is the task description to paste into the AiOrch "Task Description" field when creating the session.

---

Build a production-grade multi-tenant invoice management API with Python FastAPI and SQLite.

## Agent 1 — Database Layer
Create the database foundation:
- `app/database.py`: SQLite connection manager with WAL mode, get_db() context manager, init_db()
- `app/schema.py`: Schema with 4 tables — tenants (id, name, api_key, is_active), clients (id, tenant_id, name, email, address, phone), invoices (id, tenant_id, client_id, invoice_number, status, issue_date, due_date, subtotal, tax_rate, tax_amount, total, notes), line_items (id, invoice_id, description, quantity, unit_price, amount, sort_order)
- `app/models.py`: Pydantic v2 models for all entities (Create, Response, List variants)
- `app/seed.py`: Demo data — 2 tenants, 6 clients, 10 invoices in various statuses, 25+ line items with correct calculations
- `requirements.txt` and `.env.example`
- DATABASE_URL from environment, no fallbacks, file permissions 0o600

## Agent 2 — API Layer
Build full REST endpoints:
- `app/main.py`: FastAPI app, lifespan calls init_db() + optional seed, health check at GET /health
- `app/routes/tenants.py`: CRUD (POST 201, GET list, GET by id, PUT, DELETE 204). API key only shown in POST response. Tenant endpoints do NOT require X-Tenant-ID or X-API-Key headers (admin-level).
- `app/routes/clients.py`: CRUD scoped by X-Tenant-ID header. Search by name, pagination (limit/offset).
- `app/routes/invoices.py`: CRUD with line items in create/get. Filters: status, client_id, date_from, date_to (ISO YYYY-MM-DD). PATCH /status endpoint. POST /mark-overdue endpoint. Invoice number and status validation: import from app.services (agent 3) — create stubs if not available yet.
- `app/routes/line_items.py`: Add/update/delete items on an invoice. Call recalculate_invoice() from app.services.calculations — create stub if not available yet. Do NOT inline recalculation logic.
- Consistent error format: {"detail": "message"} with proper HTTP status codes (400, 404, 409, 422)

## Agent 3 — Business Logic
Build the invoice engine in `app/services/`:
- `invoice_number.py`: Generate INV-{YEAR}-{NNNN} format, sequential per tenant per year, thread-safe
- `calculations.py`: Line item amounts (qty * price), invoice totals (subtotal + tax), all rounded to 2 decimal places. recalculate_invoice() updates the database.
- `status.py`: Validate transitions (draft→sent→paid, paid/cancelled are terminal). Raise ValueError for invalid transitions.
- `overdue.py`: Single UPDATE query to mark sent invoices past due_date as overdue
- `pdf.py`: Generate formatted plain-text invoice document with itemised table
- No HTTP/FastAPI imports in services — pure business logic

## Agent 4 — Security and Testing
Add security middleware and comprehensive tests:
- `app/middleware/tenant.py`: FastAPI dependency — validate X-Tenant-ID + X-API-Key headers against database. 401 for invalid, 403 for deactivated tenant. All client/invoice/line_item endpoints use this dependency.
- `app/middleware/rate_limit.py`: Per-IP sliding window, RATE_LIMIT_RPM from env, 429 with Retry-After header, exempt /health
- CORS middleware in main.py
- `tests/conftest.py`: Fixtures with temporary SQLite database per test session
- `tests/test_api.py`: 20+ integration tests covering: tenant CRUD, client CRUD with tenant isolation, invoice creation with line items and correct totals, status transitions (valid + invalid), line item recalculation, API key auth (missing/wrong/deactivated), pagination, health check
- `README.md`: Quick start, endpoint table, auth docs, env vars, project structure

All tests must pass: `pytest tests/ -v`
