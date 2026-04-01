# Database Schema and Setup — Agent 1

## Overview

Create the SQLite database layer for a multi-tenant invoice management system. This includes the schema design (4 tables with relationships), connection management with WAL mode, a database initialisation module, and seed data for demo purposes.

This agent's output is the foundation — agents 2, 3, and 4 all import from this module.

## Implementation

### Task 1: Database connection module

**File**: `app/database.py`

Create a SQLite connection manager that:
- Reads `DATABASE_URL` from environment (path to SQLite file, e.g., `sqlite:///data/invoices.db`)
- Enables WAL journal mode for concurrent reads
- Sets busy timeout to 5000ms
- Creates parent directories if they don't exist
- Sets file permissions to 0o600 (owner read/write only)
- Provides a context manager `get_db()` that yields a connection with `row_factory = sqlite3.Row`
- Commits on success, rolls back on exception
- Initialises the schema on first run via `init_db()`

### Task 2: Schema definition

**File**: `app/schema.py`

Define the SQL schema as a Python constant `SCHEMA`:

```sql
CREATE TABLE IF NOT EXISTS tenants (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    api_key TEXT NOT NULL UNIQUE,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS clients (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    email TEXT,
    address TEXT,
    phone TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS invoices (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    client_id TEXT NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    invoice_number TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'sent', 'paid', 'overdue', 'cancelled')),
    issue_date TEXT NOT NULL,
    due_date TEXT NOT NULL,
    subtotal REAL NOT NULL DEFAULT 0.0,
    tax_rate REAL NOT NULL DEFAULT 0.0,
    tax_amount REAL NOT NULL DEFAULT 0.0,
    total REAL NOT NULL DEFAULT 0.0,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(tenant_id, invoice_number)
);

CREATE TABLE IF NOT EXISTS line_items (
    id TEXT PRIMARY KEY,
    invoice_id TEXT NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    quantity REAL NOT NULL DEFAULT 1.0,
    unit_price REAL NOT NULL,
    amount REAL NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_clients_tenant ON clients(tenant_id);
CREATE INDEX IF NOT EXISTS idx_invoices_tenant ON invoices(tenant_id);
CREATE INDEX IF NOT EXISTS idx_invoices_client ON invoices(client_id);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_invoices_due_date ON invoices(tenant_id, due_date);
CREATE INDEX IF NOT EXISTS idx_line_items_invoice ON line_items(invoice_id);
```

### Task 3: Pydantic models

**File**: `app/models.py`

Define Pydantic v2 models for request/response validation:

- `TenantCreate(name: str)` — auto-generates id (uuid4) and api_key (secrets.token_urlsafe(32))
- `TenantResponse(id, name, is_active, created_at, updated_at)` — never expose api_key in list responses
- `ClientCreate(name: str, email: str | None, address: str | None, phone: str | None)`
- `ClientResponse(id, tenant_id, name, email, address, phone, created_at, updated_at)`
- `LineItemCreate(description: str, quantity: float, unit_price: float)`
- `LineItemResponse(id, invoice_id, description, quantity, unit_price, amount, sort_order, created_at)`
- `InvoiceCreate(client_id: str, issue_date: str, due_date: str, tax_rate: float = 0.0, notes: str | None, line_items: list[LineItemCreate])`
- `InvoiceResponse(id, tenant_id, client_id, invoice_number, status, issue_date, due_date, subtotal, tax_rate, tax_amount, total, notes, line_items: list[LineItemResponse], created_at, updated_at)`
- `InvoiceListResponse` — same as InvoiceResponse but without line_items (for list endpoints)
- `InvoiceStatusUpdate(status: str)` — validated against allowed transitions

### Task 4: Seed data

**File**: `app/seed.py`

Create a `seed_demo_data(db_path: str)` function that inserts:
- 2 tenants: "Acme Corp" and "Globex Inc"
- 3 clients per tenant (6 total) with realistic names
- 5 invoices per tenant (10 total) in various statuses (2 draft, 1 sent, 1 paid, 1 overdue)
- 2-4 line items per invoice with realistic descriptions and prices
- All amounts correctly calculated (subtotal = sum of line_item amounts, tax_amount = subtotal * tax_rate, total = subtotal + tax_amount)

Use `INSERT OR IGNORE` so seed data is idempotent.

### Task 5: Project setup files

**File**: `requirements.txt`
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
python-multipart>=0.0.6
pytest>=7.4.0
httpx>=0.25.0
```

**File**: `.env.example`
```
DATABASE_URL=sqlite:///data/invoices.db
API_HOST=0.0.0.0
API_PORT=8000
DEFAULT_TAX_RATE=0.20
RATE_LIMIT_RPM=60
```

**File**: `app/__init__.py` — empty

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | SQLite database file path | `sqlite:///data/invoices.db` |
| `DEFAULT_TAX_RATE` | Default tax rate for new invoices | `0.20` |

## Acceptance Criteria

### Functional
- [ ] `init_db()` creates all 4 tables with correct schema and indexes
- [ ] `get_db()` context manager handles commit/rollback correctly
- [ ] WAL mode enabled, busy timeout set to 5000ms
- [ ] Database file created with 0o600 permissions
- [ ] All Pydantic models validate input correctly
- [ ] Seed data inserts 2 tenants, 6 clients, 10 invoices, 25+ line items
- [ ] Seed data is idempotent (running twice doesn't duplicate)
- [ ] All invoice amounts are correctly calculated in seed data
- [ ] requirements.txt contains all dependencies
- [ ] .env.example contains all environment variables

### Structural
- [ ] All files in `app/` package
- [ ] No hardcoded values — all config from environment
- [ ] No fallback defaults in database module — fail if DATABASE_URL not set
- [ ] Clean imports — no circular dependencies
