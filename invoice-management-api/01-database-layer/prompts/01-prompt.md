# Orchestrator Prompt — Database Layer

Read the task file: `/opt/orchestrator/v3/sample_tasks/invoice-management-api/01-database-layer/01-database-schema-and-setup.md`

## Delivery Principals

- No hardcoding — all configuration from environment variables
- No fallbacks — if `DATABASE_URL` is not set, raise an error explicitly
- No mock data — seed data must be realistic and correctly calculated
- All Pydantic models must use v2 syntax (model_config, not class Config)
- Use uuid4 for all primary keys (stored as TEXT in SQLite)
- Seed data must be idempotent (INSERT OR IGNORE)
- File permissions 0o600 on database file after creation

## Pre-Existing Infrastructure

This is a greenfield project. The git repo at `/opt/demo-invoice-api` has only a README.md on the `main` branch. You are building from scratch.

**Python version**: 3.12
**Package manager**: pip
**Database**: SQLite (no external database required)

## What to Build

### Step 1: Project structure
Create the following files:
- `app/__init__.py` (empty)
- `app/schema.py` (SQL schema constant)
- `app/database.py` (connection manager + init_db)
- `app/models.py` (Pydantic models)
- `app/seed.py` (demo data insertion)
- `requirements.txt`
- `.env.example`

### Step 2: Schema (`app/schema.py`)
Define `SCHEMA` as a multi-line string with CREATE TABLE IF NOT EXISTS for: tenants, clients, invoices, line_items. Include all indexes. Follow the exact schema from the task file.

### Step 3: Database module (`app/database.py`)
- Read `DATABASE_URL` from `os.environ` — no default, raise `RuntimeError` if missing
- Parse the path from the sqlite:/// prefix
- Create parent directories with `mkdir(parents=True, exist_ok=True)`
- `init_db()`: connect, executescript(SCHEMA), set file permissions 0o600
- `get_db()`: context manager, set row_factory, enable WAL, busy_timeout=5000

### Step 4: Pydantic models (`app/models.py`)
Create all models listed in the task file. Key points:
- `TenantCreate`: auto-generate `id` and `api_key` in model defaults (use `Field(default_factory=...)`)
- `InvoiceCreate`: includes `line_items: list[LineItemCreate]`
- `InvoiceResponse`: includes `line_items: list[LineItemResponse]`
- `InvoiceListResponse`: same fields as InvoiceResponse but WITHOUT line_items
- `InvoiceStatusUpdate`: validate status is one of draft, sent, paid, overdue, cancelled

### Step 5: Seed data (`app/seed.py`)
- Function `seed_demo_data(db_path: str)` that directly connects to the database
- 2 tenants with generated UUIDs and API keys
- 3 clients per tenant with realistic business names
- 5 invoices per tenant with different statuses and dates
- 2-4 line items per invoice with realistic service descriptions and prices
- All amounts must be mathematically correct: amount = quantity * unit_price, subtotal = sum(amounts), tax_amount = subtotal * tax_rate, total = subtotal + tax_amount
- Use INSERT OR IGNORE for idempotency

### Step 6: requirements.txt and .env.example
Exact contents specified in the task file. No additional packages beyond what's listed.

## Verification Checklist

1. `python -c "from app.schema import SCHEMA; print('Schema OK')"` — imports without error
2. `python -c "from app.database import init_db, get_db; print('Database OK')"` — imports without error
3. `python -c "from app.models import TenantCreate, InvoiceCreate, InvoiceResponse; print('Models OK')"` — imports without error
4. All 4 tables created with correct columns and constraints
5. Indexes exist on tenant_id, client_id, status, due_date
6. Seed data inserts without errors and all amounts are correct
7. No hardcoded database paths — everything from DATABASE_URL
