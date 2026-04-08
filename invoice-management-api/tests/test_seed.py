"""Tests for seed demo data."""

import sqlite3
import tempfile
import os

from app.schema import SCHEMA
from app.seed import seed_demo_data


def _create_db() -> str:
    """Create a temporary database with the schema applied, return its path."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    return path


class TestSeedRecordCounts:
    """Verify seed_demo_data inserts the correct number of records."""

    def test_tenant_count(self):
        path = _create_db()
        try:
            seed_demo_data(path)
            conn = sqlite3.connect(path)
            count = conn.execute("SELECT COUNT(*) FROM tenants").fetchone()[0]
            conn.close()
            assert count == 2
        finally:
            os.unlink(path)

    def test_client_count(self):
        path = _create_db()
        try:
            seed_demo_data(path)
            conn = sqlite3.connect(path)
            count = conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
            conn.close()
            assert count == 6
        finally:
            os.unlink(path)

    def test_invoice_count(self):
        path = _create_db()
        try:
            seed_demo_data(path)
            conn = sqlite3.connect(path)
            count = conn.execute("SELECT COUNT(*) FROM invoices").fetchone()[0]
            conn.close()
            assert count == 10
        finally:
            os.unlink(path)

    def test_line_item_count_minimum(self):
        path = _create_db()
        try:
            seed_demo_data(path)
            conn = sqlite3.connect(path)
            count = conn.execute("SELECT COUNT(*) FROM line_items").fetchone()[0]
            conn.close()
            assert count >= 25
        finally:
            os.unlink(path)

    def test_invoices_per_tenant(self):
        path = _create_db()
        try:
            seed_demo_data(path)
            conn = sqlite3.connect(path)
            rows = conn.execute(
                "SELECT tenant_id, COUNT(*) FROM invoices GROUP BY tenant_id"
            ).fetchall()
            conn.close()
            for _, cnt in rows:
                assert cnt == 5
        finally:
            os.unlink(path)

    def test_clients_per_tenant(self):
        path = _create_db()
        try:
            seed_demo_data(path)
            conn = sqlite3.connect(path)
            rows = conn.execute(
                "SELECT tenant_id, COUNT(*) FROM clients GROUP BY tenant_id"
            ).fetchall()
            conn.close()
            for _, cnt in rows:
                assert cnt == 3
        finally:
            os.unlink(path)

    def test_invoice_statuses_per_tenant(self):
        """Each tenant should have 2 draft, 1 sent, 1 paid, 1 overdue."""
        path = _create_db()
        try:
            seed_demo_data(path)
            conn = sqlite3.connect(path)
            for tenant_id in ("t-acme-001", "t-globex-001"):
                rows = conn.execute(
                    "SELECT status, COUNT(*) FROM invoices WHERE tenant_id = ? GROUP BY status",
                    (tenant_id,),
                ).fetchall()
                status_counts = dict(rows)
                assert status_counts.get("draft") == 2
                assert status_counts.get("sent") == 1
                assert status_counts.get("paid") == 1
                assert status_counts.get("overdue") == 1
            conn.close()
        finally:
            os.unlink(path)


class TestSeedIdempotency:
    """Running seed_demo_data twice must not duplicate records."""

    def test_double_seed_no_duplicates(self):
        path = _create_db()
        try:
            seed_demo_data(path)
            seed_demo_data(path)
            conn = sqlite3.connect(path)
            tenants = conn.execute("SELECT COUNT(*) FROM tenants").fetchone()[0]
            clients = conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
            invoices = conn.execute("SELECT COUNT(*) FROM invoices").fetchone()[0]
            line_items = conn.execute("SELECT COUNT(*) FROM line_items").fetchone()[0]
            conn.close()
            assert tenants == 2
            assert clients == 6
            assert invoices == 10
            assert line_items >= 25
        finally:
            os.unlink(path)


class TestSeedAmountCalculations:
    """Verify all invoice amounts are correctly computed from line items."""

    def test_line_item_amounts(self):
        """Each line_item.amount == round(quantity * unit_price, 2)."""
        path = _create_db()
        try:
            seed_demo_data(path)
            conn = sqlite3.connect(path)
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT quantity, unit_price, amount FROM line_items").fetchall()
            conn.close()
            assert len(rows) > 0
            for row in rows:
                expected = round(row["quantity"] * row["unit_price"], 2)
                assert row["amount"] == expected, (
                    f"line item amount {row['amount']} != {expected}"
                )
        finally:
            os.unlink(path)

    def test_invoice_subtotal_matches_line_items(self):
        """invoice.subtotal == sum of its line_items.amount."""
        path = _create_db()
        try:
            seed_demo_data(path)
            conn = sqlite3.connect(path)
            conn.row_factory = sqlite3.Row
            invoices = conn.execute("SELECT id, subtotal FROM invoices").fetchall()
            for inv in invoices:
                li_sum = conn.execute(
                    "SELECT COALESCE(SUM(amount), 0) AS s FROM line_items WHERE invoice_id = ?",
                    (inv["id"],),
                ).fetchone()["s"]
                assert inv["subtotal"] == round(li_sum, 2), (
                    f"Invoice {inv['id']}: subtotal {inv['subtotal']} != line items sum {li_sum}"
                )
            conn.close()
        finally:
            os.unlink(path)

    def test_invoice_tax_and_total(self):
        """tax_amount == round(subtotal * tax_rate, 2), total == round(subtotal + tax_amount, 2)."""
        path = _create_db()
        try:
            seed_demo_data(path)
            conn = sqlite3.connect(path)
            conn.row_factory = sqlite3.Row
            invoices = conn.execute(
                "SELECT id, subtotal, tax_rate, tax_amount, total FROM invoices"
            ).fetchall()
            for inv in invoices:
                expected_tax = round(inv["subtotal"] * inv["tax_rate"], 2)
                expected_total = round(inv["subtotal"] + expected_tax, 2)
                assert inv["tax_amount"] == expected_tax, (
                    f"Invoice {inv['id']}: tax {inv['tax_amount']} != {expected_tax}"
                )
                assert inv["total"] == expected_total, (
                    f"Invoice {inv['id']}: total {inv['total']} != {expected_total}"
                )
            conn.close()
        finally:
            os.unlink(path)
