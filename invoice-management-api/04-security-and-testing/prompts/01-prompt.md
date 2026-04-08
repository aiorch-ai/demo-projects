# Orchestrator Prompt — Security, Middleware, and Testing

Read the task file: `/opt/orchestrator/v3/sample_tasks/demo-projects/invoice-management-api/04-security-and-testing/01-security-and-tests.md`

## Delivery Principals

- No hardcoding — rate limits and CORS origins from environment variables
- No fallbacks — missing required headers must return explicit 4xx errors
- No mock data — tests run against a real temporary SQLite database
- All tests must pass: `pytest tests/ -v` with zero failures
- Tenant isolation is non-negotiable — verify with cross-tenant access tests
- Rate limiting must include cleanup to prevent memory growth

## Pre-Existing Infrastructure

This agent builds on all three previous agents. The following modules are available:

1. **`app/database.py`** — `init_db()`, `get_db()` context manager
2. **`app/schema.py`** — SQL schema with tables: tenants (id, name, api_key, is_active), clients, invoices, line_items
3. **`app/models.py`** — Pydantic v2 models for all entities
4. **`app/seed.py`** — `seed_demo_data(db_path)` for populating demo data
5. **`app/main.py`** — FastAPI application with all routers included
6. **`app/routes/`** — tenants.py, clients.py, invoices.py, line_items.py with full CRUD endpoints
7. **`app/services/`** — invoice_number.py, calculations.py, status.py, overdue.py, pdf.py

**Key details about existing routes:**
- Tenant routes at `/api/tenants` — no auth required (admin-level)
- Client routes at `/api/clients` — currently expect `X-Tenant-ID` header
- Invoice routes at `/api/invoices` — currently expect `X-Tenant-ID` header
- Line item routes at `/api/invoices/{invoice_id}/items`

**What this agent adds:**
- API key authentication via `X-API-Key` header
- Tenant validation (active check) as a FastAPI dependency
- Rate limiting middleware
- CORS middleware
- pytest integration test suite
- README.md

## What to Build

### Step 1: Middleware package
Create `app/middleware/__init__.py` exporting `get_current_tenant`.

### Step 2: Tenant authentication dependency (`app/middleware/tenant.py`)
- FastAPI dependency function using `Header(...)` for X-Tenant-ID and X-API-Key
- Query: `SELECT * FROM tenants WHERE id = ? AND api_key = ?`
- If no match: raise `HTTPException(401, "Invalid tenant ID or API key")`
- If `is_active = 0`: raise `HTTPException(403, "Tenant is deactivated")`
- Return tenant row as dict
- This dependency must be added to client, invoice, and line_item routers via `Depends(get_current_tenant)`

### Step 3: Rate limiting middleware (`app/middleware/rate_limit.py`)
- Subclass `BaseHTTPMiddleware`
- In-memory dict: `{ip: [timestamp, ...]}` with sliding 60-second window
- Read `RATE_LIMIT_RPM` from environment (default 60 if not set — this is the one exception where a default is acceptable since it's a safety mechanism)
- Exempt path: `/health`
- Return `JSONResponse(429, {"detail": "Rate limit exceeded"}, headers={"Retry-After": "60"})`
- Purge stale IPs every 5 minutes to prevent memory growth

### Step 4: Wire middleware into app
Modify `app/main.py` to add middleware in this exact order (FastAPI processes middleware in reverse order — last added runs first):
1. First: `app.add_middleware(CORSMiddleware, ...)` — runs last (outermost)
2. Second: `app.add_middleware(RateLimitMiddleware, ...)` — runs before CORS
This means rate limiting is checked first, then CORS headers are added.

- Read `CORS_ORIGINS` from environment variable
- Read `RATE_LIMIT_RPM` from environment variable
- Ensure the `get_current_tenant` dependency is added to client, invoice, and line_item routers via `dependencies=[Depends(get_current_tenant)]` on the APIRouter. Do NOT add it to tenant routes — those are admin-level and open.

### Step 5: Test fixtures (`tests/conftest.py`)
```python
import os
import tempfile
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def db_path():
    """Create a temporary database file."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.unlink(path)

@pytest.fixture
def client(db_path):
    """Test client with fresh database."""
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    # Re-import app to pick up new DATABASE_URL
    # init_db() and seed_demo_data()
    # yield TestClient(app)
```

### Step 6: Test cases (`tests/test_api.py`)
Write all 20+ tests listed in the task file. Key patterns:
- Create a tenant via POST, capture the api_key from response
- Use that api_key + tenant_id as headers for all subsequent requests
- For isolation tests: create 2 tenants, verify each can only see their own data
- For calculation tests: create invoice with known line items, verify totals match
- For status tests: create draft invoice, transition to sent (should work), then try draft (should fail 400)

### Step 7: README.md
Replace the initial README with full documentation. Include:
- Project title and description
- Quick start with exact commands
- Complete endpoint table
- Authentication section explaining X-Tenant-ID + X-API-Key
- Environment variables table
- Test instructions
- ASCII project structure tree

## Verification Checklist

1. `pytest tests/ -v` — all 20+ tests pass
2. Request without X-API-Key to /api/clients returns 401
3. Request with wrong API key returns 401
4. Deactivated tenant returns 403
5. Tenant A's key cannot fetch tenant B's invoices (returns 401 or empty)
6. Rate limit test: send RATE_LIMIT_RPM+1 requests, last one returns 429
7. GET /health works without any auth headers
8. CORS headers present in response
9. README.md renders correctly with all sections
