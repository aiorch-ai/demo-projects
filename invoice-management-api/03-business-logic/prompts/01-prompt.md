# Orchestrator Prompt — Business Logic Engine

Read the task file: `/opt/orchestrator/v3/sample_tasks/invoice-management-api/03-business-logic/01-invoice-engine.md`

## Delivery Principals

- No hardcoding — tax rates from environment, date handling via standard library
- No fallbacks — raise explicit errors for invalid states
- No mock data — all functions operate on real database connections
- All monetary calculations must use `round(value, 2)` — floating-point drift is unacceptable
- Pure functions where possible — status validation and calculations should have no side effects
- Database functions accept `sqlite3.Connection` as a parameter — never create their own connections

## Pre-Existing Infrastructure

This agent builds on the database layer (agent 1). The following modules are available:

1. **`app/database.py`** — `get_db()` yields a sqlite3.Connection with row_factory=sqlite3.Row
2. **`app/schema.py`** — Schema with tables: tenants, clients, invoices (with subtotal, tax_rate, tax_amount, total columns), line_items (with quantity, unit_price, amount columns)
3. **`app/models.py`** — Pydantic models including InvoiceCreate, InvoiceResponse, InvoiceStatusUpdate

**Database columns relevant to this agent:**
- `invoices.invoice_number` — TEXT, UNIQUE per tenant (tenant_id, invoice_number)
- `invoices.status` — TEXT, CHECK constraint: draft, sent, paid, overdue, cancelled
- `invoices.subtotal`, `tax_rate`, `tax_amount`, `total` — REAL
- `invoices.issue_date`, `due_date` — TEXT (ISO format YYYY-MM-DD)
- `line_items.quantity`, `unit_price`, `amount` — REAL

## What to Build

### Step 1: Services package
Create `app/services/__init__.py` with exports from all service modules.

### Step 2: Invoice numbering (`app/services/invoice_number.py`)
- Query: `SELECT invoice_number FROM invoices WHERE tenant_id = ? AND invoice_number LIKE 'INV-{year}-%' ORDER BY invoice_number DESC LIMIT 1`
- Parse the sequence number from the last invoice_number, increment by 1
- If no invoices exist for this year, start at 0001
- Format: `f"INV-{year}-{sequence:04d}"`
- Use the current year from `datetime.now().year`

### Step 3: Amount calculations (`app/services/calculations.py`)
- `calculate_line_item_amount(quantity, unit_price)` → `round(quantity * unit_price, 2)`
- `calculate_invoice_totals(line_items)` → sum amounts, apply tax_rate, round each field
- `recalculate_invoice(db, invoice_id)` → SELECT all line_items for invoice, calculate totals, UPDATE invoices SET subtotal=?, tax_amount=?, total=?, updated_at=datetime('now')

### Step 4: Status transitions (`app/services/status.py`)
- Define `ALLOWED_TRANSITIONS` dict mapping each status to list of allowed next statuses
- `validate_status_transition(current, new)` → return True/False
- `get_allowed_transitions(current)` → return list
- Raise `ValueError` with descriptive message for invalid transitions

### Step 5: Overdue detection (`app/services/overdue.py`)
- Single UPDATE query: `UPDATE invoices SET status = 'overdue', updated_at = datetime('now') WHERE status = 'sent' AND due_date < date('now')`
- Add `AND tenant_id = ?` if tenant_id is provided
- Return the number of rows affected via `cursor.rowcount`

### Step 6: Invoice document (`app/services/pdf.py`)
- Accept dicts for invoice, client, tenant, line_items
- Format a plain-text document with box-drawing characters
- Include: header with invoice number, from/to addresses, date/due/status, itemised table with columns, subtotal/tax/total summary, notes
- Return as UTF-8 encoded bytes

## Verification Checklist

1. `python -c "from app.services import generate_invoice_number, calculate_invoice_totals, validate_status_transition, mark_overdue_invoices, generate_invoice_document; print('Services OK')"` — all imports work
2. Invoice numbering generates sequential numbers: INV-2025-0001, INV-2025-0002, etc.
3. `calculate_line_item_amount(10, 150.00)` returns `1500.00`
4. `calculate_invoice_totals([{"amount": 1500.00}, {"amount": 400.00}])` with tax_rate 0.20 returns subtotal=1900.00, tax_amount=380.00, total=2280.00
5. `validate_status_transition("draft", "sent")` returns True
6. `validate_status_transition("paid", "draft")` raises ValueError
7. Overdue detection only affects 'sent' invoices past due date
8. Invoice document output is readable and correctly formatted
