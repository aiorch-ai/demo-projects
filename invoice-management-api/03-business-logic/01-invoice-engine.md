# Invoice Business Logic Engine — Agent 3

## Overview

Build the business logic layer that handles invoice-specific operations: auto-numbering, amount calculations, status transition validation, overdue detection, and PDF invoice generation. This module is imported by the API layer but contains no HTTP-specific code.

## Implementation

### Task 1: Invoice numbering service

**File**: `app/services/invoice_number.py`

Generate invoice numbers in the format: `INV-{YEAR}-{SEQUENCE}`

- `YEAR`: 4-digit current year
- `SEQUENCE`: 4-digit zero-padded sequence number, scoped per tenant per year
- Example: `INV-2025-0001`, `INV-2025-0002`
- Query the database for the highest existing sequence number for the tenant in the current year
- Thread-safe: use a database transaction to read and increment atomically

Function signature:
```python
def generate_invoice_number(db: sqlite3.Connection, tenant_id: str) -> str:
```

### Task 2: Amount calculation service

**File**: `app/services/calculations.py`

Functions:
```python
def calculate_line_item_amount(quantity: float, unit_price: float) -> float:
    """Calculate amount = quantity * unit_price, rounded to 2 decimal places."""

def calculate_invoice_totals(line_items: list[dict]) -> dict:
    """Calculate subtotal, tax_amount, total from line items.
    
    Returns: {"subtotal": float, "tax_amount": float, "total": float}
    Each value rounded to 2 decimal places.
    """

def recalculate_invoice(db: sqlite3.Connection, invoice_id: str) -> None:
    """Recalculate and update invoice totals from its current line items."""
```

All monetary calculations must use `round(value, 2)` to avoid floating-point drift.

### Task 3: Status transition validator

**File**: `app/services/status.py`

Define allowed status transitions:

```
draft    → sent, cancelled
sent     → paid, overdue, cancelled
paid     → (terminal — no transitions allowed)
overdue  → paid, cancelled
cancelled → (terminal — no transitions allowed)
```

Functions:
```python
def validate_status_transition(current: str, new: str) -> bool:
    """Return True if transition is allowed, False otherwise."""

def get_allowed_transitions(current: str) -> list[str]:
    """Return list of statuses the invoice can transition to."""
```

Raise `ValueError` with a clear message if an invalid transition is attempted (e.g., "Cannot transition from 'paid' to 'draft'. Invoice is in a terminal state.").

### Task 4: Overdue detection

**File**: `app/services/overdue.py`

Function:
```python
def mark_overdue_invoices(db: sqlite3.Connection, tenant_id: str | None = None) -> int:
    """Find all 'sent' invoices with due_date < today and update status to 'overdue'.
    
    If tenant_id is provided, only check that tenant's invoices.
    Returns the number of invoices marked as overdue.
    """
```

This function should be called periodically or on-demand. Uses a single UPDATE query with WHERE clause, not a loop.

### Task 5: PDF invoice generation

**File**: `app/services/pdf.py`

Generate a simple text-based invoice document. Since this is a demo, use plain text formatted to look like an invoice (not a full PDF library). Return bytes that can be served as `application/pdf` content type or as `text/plain`.

Function:
```python
def generate_invoice_document(invoice: dict, client: dict, tenant: dict, line_items: list[dict]) -> bytes:
    """Generate a formatted invoice document as UTF-8 bytes.
    
    Format:
    ─────────────────────────────────────
    INVOICE {invoice_number}
    ─────────────────────────────────────
    From: {tenant_name}
    To:   {client_name}
          {client_address}
          {client_email}
    
    Date:     {issue_date}
    Due Date: {due_date}
    Status:   {status}
    ─────────────────────────────────────
    
    # | Description        | Qty | Price  | Amount
    ──┼────────────────────┼─────┼────────┼───────
    1 | Web development    | 10  | 150.00 | 1500.00
    2 | Design services    |  5  |  80.00 |  400.00
    ─────────────────────────────────────
                              Subtotal: 1900.00
                              Tax (20%):  380.00
                              TOTAL:    2280.00
    ─────────────────────────────────────
    
    Notes: {notes}
    """
```

### Task 6: Services package init

**File**: `app/services/__init__.py`

Export the main functions:
```python
from app.services.invoice_number import generate_invoice_number
from app.services.calculations import calculate_line_item_amount, calculate_invoice_totals, recalculate_invoice
from app.services.status import validate_status_transition, get_allowed_transitions
from app.services.overdue import mark_overdue_invoices
from app.services.pdf import generate_invoice_document
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEFAULT_TAX_RATE` | Default tax rate for new invoices | `0.20` |

## Acceptance Criteria

### Functional
- [ ] Invoice numbers generated in INV-{YEAR}-{NNNN} format, sequential per tenant per year
- [ ] Amount calculations correct: amount = qty * price, subtotal = sum(amounts), tax = subtotal * rate, total = subtotal + tax
- [ ] All monetary values rounded to 2 decimal places
- [ ] Status transitions validated: draft→sent→paid is allowed, paid→draft is rejected
- [ ] Terminal states (paid, cancelled) reject all transitions with clear error message
- [ ] Overdue detection updates sent invoices past due date in a single query
- [ ] Invoice document generation produces readable formatted output
- [ ] recalculate_invoice updates the database row correctly

### Structural
- [ ] All business logic in `app/services/` — no HTTP/FastAPI imports
- [ ] Pure functions where possible (calculations, status validation)
- [ ] Database functions accept connection as parameter (dependency injection)
- [ ] No hardcoded tax rates or date formats
