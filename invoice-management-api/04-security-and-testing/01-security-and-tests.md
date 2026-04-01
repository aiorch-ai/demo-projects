# Security, Middleware, and Testing — Agent 4

## Overview

Build the security layer (tenant isolation middleware, API key authentication, rate limiting) and a comprehensive pytest test suite that covers all endpoints. This agent depends on agents 1-3 completing first, as it writes integration tests against the real API.

## Implementation

### Task 1: Tenant isolation middleware

**File**: `app/middleware/tenant.py`

Create a FastAPI dependency that extracts and validates the tenant from the request:

```python
def get_current_tenant(
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: sqlite3.Connection = Depends(get_db),
) -> dict:
```

Validation:
- `X-Tenant-ID` header is required — return 400 if missing
- `X-API-Key` header is required — return 401 if missing
- Look up tenant by id AND api_key — return 401 if no match
- Check `is_active = 1` — return 403 if tenant is deactivated
- Return the tenant row as a dict

All client, invoice, and line_item endpoints must use this dependency. The tenant_id from the dependency is used to scope all queries — never trust a tenant_id from the URL or request body.

### Task 2: Rate limiting middleware

**File**: `app/middleware/rate_limit.py`

Create a simple in-memory per-IP rate limiter:
- Track request timestamps per client IP
- Sliding window of 60 seconds
- Max requests configurable via `RATE_LIMIT_RPM` environment variable
- Return 429 with `{"detail": "Rate limit exceeded"}` and `Retry-After: 60` header
- Exempt `/health` endpoint
- Clean up stale entries periodically to prevent memory growth

Implement as a Starlette middleware (BaseHTTPMiddleware).

### Task 3: CORS configuration

In `app/main.py`, add CORS middleware:
- Allow origins: `*` (configurable via `CORS_ORIGINS` env var)
- Allow methods: GET, POST, PUT, PATCH, DELETE, OPTIONS
- Allow headers: `*`
- Allow credentials: false

### Task 4: Middleware package

**File**: `app/middleware/__init__.py`

Export `get_current_tenant` for use as a FastAPI dependency.

### Task 5: Integration test suite

**File**: `tests/test_api.py`

Write pytest tests using `httpx.AsyncClient` with FastAPI's `TestClient` (or `ASGITransport`). Use a temporary SQLite database for each test session (via pytest fixture).

**Test fixture** (`tests/conftest.py`):
```python
@pytest.fixture
def client():
    """Create a test client with a fresh temporary database."""
    # Set DATABASE_URL to a temp file
    # Import and create the app
    # Seed test data
    # Yield TestClient
    # Clean up temp file
```

**Required test cases** (minimum 20 tests):

**Tenant tests:**
- `test_create_tenant` — POST /api/tenants returns 201 with id and api_key
- `test_list_tenants` — GET /api/tenants returns list without api_key
- `test_get_tenant` — GET /api/tenants/{id} returns correct tenant
- `test_delete_tenant` — DELETE /api/tenants/{id} returns 204, tenant gone

**Client tests:**
- `test_create_client` — POST /api/clients with valid tenant headers returns 201
- `test_list_clients` — GET /api/clients returns only the authenticated tenant's clients
- `test_client_tenant_isolation` — tenant A cannot see tenant B's clients
- `test_client_search` — GET /api/clients?search=name filters correctly

**Invoice tests:**
- `test_create_invoice_with_line_items` — POST /api/invoices creates invoice + items, amounts correct
- `test_list_invoices_filter_status` — GET /api/invoices?status=draft returns only drafts
- `test_list_invoices_filter_date` — GET /api/invoices?date_from=X&date_to=Y filters by date
- `test_get_invoice_includes_line_items` — GET /api/invoices/{id} includes line_items array
- `test_invoice_number_auto_generated` — created invoice has INV-{year}-NNNN format
- `test_invoice_totals_calculated` — subtotal, tax, total are correct
- `test_status_transition_valid` — PATCH to 'sent' from 'draft' succeeds
- `test_status_transition_invalid` — PATCH to 'draft' from 'paid' returns 400

**Line item tests:**
- `test_add_line_item_recalculates` — POST item, invoice totals updated
- `test_delete_line_item_recalculates` — DELETE item, invoice totals updated

**Security tests:**
- `test_missing_api_key_returns_401` — request without X-API-Key gets 401
- `test_wrong_api_key_returns_401` — request with wrong key gets 401
- `test_inactive_tenant_returns_403` — deactivated tenant gets 403
- `test_tenant_isolation` — tenant A's API key cannot access tenant B's invoices

**General tests:**
- `test_health_check` — GET /health returns 200
- `test_pagination` — limit/offset work correctly

### Task 6: README

**File**: `README.md`

Write a comprehensive README with:
- Project description (1-2 sentences)
- Quick start (pip install, set env vars, run uvicorn)
- API endpoint table with method, path, description
- Authentication section (X-Tenant-ID + X-API-Key headers)
- Environment variables table
- Running tests (`pytest tests/`)
- Project structure tree

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `RATE_LIMIT_RPM` | Max requests per minute per IP | `60` |
| `CORS_ORIGINS` | Allowed CORS origins | `*` |

## Acceptance Criteria

### Security
- [ ] All client/invoice/line_item endpoints require X-Tenant-ID and X-API-Key headers
- [ ] Invalid or missing API key returns 401
- [ ] Deactivated tenant returns 403
- [ ] Tenant A cannot access tenant B's data through any endpoint
- [ ] Rate limiting returns 429 with Retry-After header when exceeded

### Testing
- [ ] pytest suite has 20+ test cases
- [ ] Tests use a temporary database (no shared state between tests)
- [ ] All tests pass: `pytest tests/ -v`
- [ ] Tenant isolation verified in tests
- [ ] Invoice calculations verified in tests
- [ ] Status transitions verified in tests

### Documentation
- [ ] README.md includes quick start, endpoint table, auth docs, env vars
- [ ] README.md includes project structure tree
