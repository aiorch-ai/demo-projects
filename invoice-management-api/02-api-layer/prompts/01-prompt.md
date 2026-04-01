# Orchestrator Prompt — API Layer

Read the task file: `/opt/orchestrator/v3/sample_tasks/invoice-management-api/02-api-layer/01-rest-endpoints.md`

## Delivery Principals

- No hardcoding — all configuration from environment variables
- No fallbacks — fail explicitly if required env vars are missing
- No mock data — all endpoints read from and write to real SQLite database
- Use proper HTTP status codes (201 for creation, 204 for deletion, 400/404/409 for errors)
- All list endpoints must support pagination (limit/offset)
- Consistent error response format: `{"detail": "message"}`

## Pre-Existing Infrastructure

This agent builds on the database layer (agent 1). The following modules are available:

1. **`app/database.py`** — `init_db()` creates tables, `get_db()` yields a database connection
2. **`app/schema.py`** — SQL schema constant (4 tables: tenants, clients, invoices, line_items)
3. **`app/models.py`** — Pydantic v2 models for all entities (TenantCreate, TenantResponse, ClientCreate, ClientResponse, InvoiceCreate, InvoiceResponse, InvoiceListResponse, LineItemCreate, LineItemResponse, InvoiceStatusUpdate)
4. **`app/seed.py`** — `seed_demo_data(db_path)` inserts demo data
5. **`requirements.txt`** — FastAPI, uvicorn, pydantic, pydantic-settings, pytest, httpx
6. **`.env.example`** — DATABASE_URL, API_HOST, API_PORT, DEFAULT_TAX_RATE, RATE_LIMIT_RPM

## What to Build

### Step 1: Routes package
Create `app/routes/__init__.py` (empty).

### Step 2: Tenant routes (`app/routes/tenants.py`)
- APIRouter with prefix `/api/tenants` and tag "tenants"
- 5 endpoints: POST, GET list, GET by id, PUT, DELETE
- POST generates uuid4 id and token_urlsafe API key
- GET list and GET by id never return the api_key field
- POST response includes api_key (only time it's visible)
- DELETE returns 204 (no content)

### Step 3: Client routes (`app/routes/clients.py`)
- APIRouter with prefix `/api/clients` and tag "clients"
- All endpoints extract `tenant_id` from `X-Tenant-ID` header (required)
- 5 endpoints: POST, GET list, GET by id, PUT, DELETE
- GET list supports `search` (LIKE query on name), `limit`, `offset`
- All queries filter by tenant_id — a client belongs to exactly one tenant

### Step 4: Invoice routes (`app/routes/invoices.py`)
- APIRouter with prefix `/api/invoices` and tag "invoices"
- All endpoints extract `tenant_id` from `X-Tenant-ID` header
- POST creates invoice + all line items in a single transaction
- Invoice number: import and call `generate_invoice_number(db, tenant_id)` from `app.services.invoice_number`. This module is built by agent 3 (business logic). If it doesn't exist yet, create a temporary stub at `app/services/invoice_number.py` with `def generate_invoice_number(db, tenant_id): import uuid; return f"INV-TEMP-{uuid.uuid4().hex[:8]}"` — agent 3 will replace it with the real implementation
- GET by id returns invoice with all line_items populated
- GET list returns InvoiceListResponse (no line_items) with filters: status, client_id, date_from, date_to, limit, offset. All dates are ISO format YYYY-MM-DD.
- PATCH /status: import and call `validate_status_transition(current, new)` from `app.services.status`. If it doesn't exist yet, create a temporary stub at `app/services/status.py` with `def validate_status_transition(current, new): return True` — agent 3 will replace it
- DELETE returns 204

### Step 5: Line item routes (`app/routes/line_items.py`)
- APIRouter with prefix `/api/invoices/{invoice_id}/items` and tag "line_items"
- POST adds a line item, then calls `recalculate_invoice(db, invoice_id)` from `app.services.calculations`
- PUT updates a line item, then calls `recalculate_invoice(db, invoice_id)`
- DELETE removes a line item, then calls `recalculate_invoice(db, invoice_id)`
- If `app.services.calculations` doesn't exist yet (agent 3 hasn't run), create a temporary stub at `app/services/calculations.py` with: `def recalculate_invoice(db, invoice_id): pass` — agent 3 will replace it with the real implementation
- Do NOT inline the recalculation logic — always call the service function

### Step 6: Main application (`app/main.py`)
- Create FastAPI app with title "Invoice Management API", version "1.0.0"
- Lifespan: call init_db() on startup, optionally seed demo data if the tenants table is empty
- Include all 4 routers
- `GET /health` returns `{"status": "ok", "version": "1.0.0"}`
- Read API_HOST and API_PORT from environment for uvicorn

## Verification Checklist

1. `python -c "from app.main import app; print('App OK')"` — imports without error
2. All 4 routers registered with correct prefixes
3. POST /api/tenants returns 201 with id and api_key
4. GET /api/tenants returns list without api_key field
5. POST /api/invoices creates invoice with line items in one request
6. GET /api/invoices supports status, client_id, date_from, date_to filters
7. Adding/removing line items recalculates invoice totals
8. 404 returned for non-existent resources
9. GET /health returns 200
