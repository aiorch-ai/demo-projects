# REST API Endpoints — Agent 2

## Overview

Build the complete REST API layer using FastAPI. This includes CRUD endpoints for all four entities (tenants, clients, invoices, line items), filtering and pagination support, proper HTTP status codes, and consistent error responses. The main FastAPI application entry point (`app/main.py`) is also created here.

This agent reads models and database utilities from agent 1's work.

## Implementation

### Task 1: FastAPI application entry point

**File**: `app/main.py`

Create the FastAPI app with:
- Title: "Invoice Management API"
- Version: "1.0.0"
- Lifespan handler that calls `init_db()` on startup and `seed_demo_data()` if database is empty
- Include all routers from the endpoint modules
- Health check endpoint at `GET /health` returning `{"status": "ok"}`

### Task 2: Tenant endpoints

**Important**: Tenant endpoints do NOT require `X-Tenant-ID` or `X-API-Key` headers. These are admin-level endpoints. In production you would add API gateway protection, but for this demo they are open. All other entity endpoints (clients, invoices, line_items) require `X-Tenant-ID` header.

**File**: `app/routes/tenants.py`

| Method | Path | Description | Response |
|--------|------|-------------|----------|
| POST | `/api/tenants` | Create tenant | 201 + TenantResponse |
| GET | `/api/tenants` | List tenants | 200 + list[TenantResponse] |
| GET | `/api/tenants/{tenant_id}` | Get tenant | 200 + TenantResponse |
| PUT | `/api/tenants/{tenant_id}` | Update tenant | 200 + TenantResponse |
| DELETE | `/api/tenants/{tenant_id}` | Delete tenant | 204 |

Notes:
- POST auto-generates uuid4 id and secrets.token_urlsafe(32) API key
- API key only shown in POST response (creation), never in GET/list
- DELETE cascades to all clients, invoices, and line items

### Task 3: Client endpoints

**File**: `app/routes/clients.py`

All client endpoints are scoped to a tenant via `X-Tenant-ID` header.

| Method | Path | Description | Response |
|--------|------|-------------|----------|
| POST | `/api/clients` | Create client | 201 + ClientResponse |
| GET | `/api/clients` | List clients for tenant | 200 + list[ClientResponse] |
| GET | `/api/clients/{client_id}` | Get client | 200 + ClientResponse |
| PUT | `/api/clients/{client_id}` | Update client | 200 + ClientResponse |
| DELETE | `/api/clients/{client_id}` | Delete client | 204 |

Query parameters for list:
- `search` (str, optional) — filter by name (LIKE %search%)
- `limit` (int, default 50, max 100)
- `offset` (int, default 0)

### Task 4: Invoice endpoints

**File**: `app/routes/invoices.py`

All invoice endpoints are scoped to a tenant via `X-Tenant-ID` header.

| Method | Path | Description | Response |
|--------|------|-------------|----------|
| POST | `/api/invoices` | Create invoice with line items | 201 + InvoiceResponse |
| GET | `/api/invoices` | List invoices for tenant | 200 + list[InvoiceListResponse] |
| GET | `/api/invoices/{invoice_id}` | Get invoice with line items | 200 + InvoiceResponse |
| PUT | `/api/invoices/{invoice_id}` | Update invoice metadata | 200 + InvoiceResponse |
| PATCH | `/api/invoices/{invoice_id}/status` | Update invoice status | 200 + InvoiceResponse |
| DELETE | `/api/invoices/{invoice_id}` | Delete invoice | 204 |

Query parameters for list:
- `status` (str, optional) — filter by status (draft, sent, paid, overdue, cancelled)
- `client_id` (str, optional) — filter by client
- `date_from` (str, optional) — issue_date >= date_from
- `date_to` (str, optional) — issue_date <= date_to
- `limit` (int, default 50, max 100)
- `offset` (int, default 0)

POST creates the invoice AND all line items in a single transaction. Invoice number is auto-generated.

### Task 5: Line item endpoints

**File**: `app/routes/line_items.py`

| Method | Path | Description | Response |
|--------|------|-------------|----------|
| POST | `/api/invoices/{invoice_id}/items` | Add line item | 201 + LineItemResponse |
| PUT | `/api/invoices/{invoice_id}/items/{item_id}` | Update line item | 200 + LineItemResponse |
| DELETE | `/api/invoices/{invoice_id}/items/{item_id}` | Delete line item | 204 |

After any line item change (add/update/delete), recalculate the invoice subtotal, tax_amount, and total.

### Task 5b: Overdue detection endpoint

Add to the invoice routes:

| Method | Path | Description | Response |
|--------|------|-------------|----------|
| POST | `/api/invoices/mark-overdue` | Mark overdue invoices | 200 + count |

This endpoint calls `mark_overdue_invoices(db, tenant_id)` from `app.services.overdue` and returns `{"marked": count}`. If the service module doesn't exist yet, create a stub that returns 0.

### Task 6: Error responses

All error responses must follow a consistent format:
```json
{
    "detail": "Human-readable error message"
}
```

Standard HTTP status codes:
- 400: Bad request (invalid input, invalid status transition)
- 404: Resource not found
- 409: Conflict (duplicate invoice number)
- 422: Validation error (Pydantic)

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_HOST` | Server bind address | `0.0.0.0` |
| `API_PORT` | Server port | `8000` |

### Date Format
All date parameters (`date_from`, `date_to`, `issue_date`, `due_date`) use ISO format: `YYYY-MM-DD`.

## Acceptance Criteria

### Functional
- [ ] All 16 endpoints respond with correct status codes
- [ ] Tenant CRUD works (create, list, get, update, delete)
- [ ] Client CRUD works with tenant scoping via X-Tenant-ID header
- [ ] Invoice CRUD works with tenant scoping, including line items in create/get
- [ ] Line item add/update/delete triggers invoice recalculation
- [ ] Invoice list supports filtering by status, client_id, date range
- [ ] Client list supports search by name
- [ ] Pagination works (limit/offset) with max limit enforcement
- [ ] Error responses are consistent JSON format
- [ ] Health check at GET /health returns 200

### Structural
- [ ] Routes organised in `app/routes/` package with separate files per entity
- [ ] All routes use dependency injection for database access
- [ ] No business logic in route handlers — delegates to service functions where needed
- [ ] No hardcoded values
