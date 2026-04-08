"""Seed demo data for the invoice management database."""

import sqlite3


def seed_demo_data(db_path: str) -> None:
    """Insert deterministic demo data into the database at db_path.

    Uses INSERT OR IGNORE for idempotency — safe to call multiple times.
    """
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")

        # ---------- tenants ----------
        tenants = [
            ("t-acme-001", "Acme Corp", "acme_test_key_xxxxx", 1),
            ("t-globex-001", "Globex Inc", "globex_test_key_xxxxx", 1),
        ]
        conn.executemany(
            "INSERT OR IGNORE INTO tenants (id, name, api_key, is_active) VALUES (?, ?, ?, ?)",
            tenants,
        )

        # ---------- clients ----------
        clients = [
            # Acme clients
            ("c-acme-001", "t-acme-001", "Wayne Enterprises", "wayne@example.com", "123 Gotham Ave", "555-0101"),
            ("c-acme-002", "t-acme-001", "Stark Industries", "stark@example.com", "200 Park Ave", "555-0102"),
            ("c-acme-003", "t-acme-001", "Daily Planet", "planet@example.com", "1 News Plaza", "555-0103"),
            # Globex clients
            ("c-globex-001", "t-globex-001", "Umbrella Corp", "umbrella@example.com", "400 Raccoon St", "555-0201"),
            ("c-globex-002", "t-globex-001", "Cyberdyne Systems", "cyberdyne@example.com", "18144 El Camino Real", "555-0202"),
            ("c-globex-003", "t-globex-001", "Initech", "initech@example.com", "4120 Freidrich Ln", "555-0203"),
        ]
        conn.executemany(
            "INSERT OR IGNORE INTO clients (id, tenant_id, name, email, address, phone) VALUES (?, ?, ?, ?, ?, ?)",
            clients,
        )

        # ---------- invoices & line items ----------
        # Define line items per invoice, then compute amounts.
        invoice_specs = [
            # Acme invoices
            {
                "id": "inv-acme-001", "tenant_id": "t-acme-001", "client_id": "c-acme-001",
                "invoice_number": "INV-001", "status": "draft",
                "issue_date": "2026-03-01", "due_date": "2026-03-31", "tax_rate": 0.10,
                "notes": "Website redesign project",
                "items": [
                    ("li-acme-001-1", "Web Development Services", 40, 150.00),
                    ("li-acme-001-2", "UI/UX Design", 20, 120.00),
                    ("li-acme-001-3", "Project Management", 10, 100.00),
                ],
            },
            {
                "id": "inv-acme-002", "tenant_id": "t-acme-001", "client_id": "c-acme-002",
                "invoice_number": "INV-002", "status": "draft",
                "issue_date": "2026-03-05", "due_date": "2026-04-04", "tax_rate": 0.10,
                "notes": "Cloud migration phase 1",
                "items": [
                    ("li-acme-002-1", "Cloud Hosting - Monthly", 3, 499.99),
                    ("li-acme-002-2", "Database Migration", 15, 175.00),
                ],
            },
            {
                "id": "inv-acme-003", "tenant_id": "t-acme-001", "client_id": "c-acme-003",
                "invoice_number": "INV-003", "status": "sent",
                "issue_date": "2026-02-15", "due_date": "2026-03-17", "tax_rate": 0.08,
                "notes": "Content management system",
                "items": [
                    ("li-acme-003-1", "API Integration", 25, 160.00),
                    ("li-acme-003-2", "Security Audit", 8, 200.00),
                    ("li-acme-003-3", "Documentation", 5, 90.00),
                ],
            },
            {
                "id": "inv-acme-004", "tenant_id": "t-acme-001", "client_id": "c-acme-001",
                "invoice_number": "INV-004", "status": "paid",
                "issue_date": "2026-01-10", "due_date": "2026-02-09", "tax_rate": 0.10,
                "notes": "Initial consultation and setup",
                "items": [
                    ("li-acme-004-1", "Technical Consultation", 12, 200.00),
                    ("li-acme-004-2", "Environment Setup", 8, 150.00),
                ],
            },
            {
                "id": "inv-acme-005", "tenant_id": "t-acme-001", "client_id": "c-acme-002",
                "invoice_number": "INV-005", "status": "overdue",
                "issue_date": "2026-01-01", "due_date": "2026-01-31", "tax_rate": 0.10,
                "notes": "Q4 maintenance contract",
                "items": [
                    ("li-acme-005-1", "Server Maintenance", 20, 130.00),
                    ("li-acme-005-2", "Performance Optimization", 10, 180.00),
                    ("li-acme-005-3", "Bug Fixes", 15, 140.00),
                    ("li-acme-005-4", "On-call Support", 5, 250.00),
                ],
            },
            # Globex invoices
            {
                "id": "inv-globex-001", "tenant_id": "t-globex-001", "client_id": "c-globex-001",
                "invoice_number": "INV-001", "status": "draft",
                "issue_date": "2026-03-10", "due_date": "2026-04-09", "tax_rate": 0.07,
                "notes": "Security infrastructure upgrade",
                "items": [
                    ("li-globex-001-1", "Security Audit", 16, 225.00),
                    ("li-globex-001-2", "Firewall Configuration", 8, 190.00),
                ],
            },
            {
                "id": "inv-globex-002", "tenant_id": "t-globex-001", "client_id": "c-globex-002",
                "invoice_number": "INV-002", "status": "draft",
                "issue_date": "2026-03-12", "due_date": "2026-04-11", "tax_rate": 0.07,
                "notes": "AI model deployment",
                "items": [
                    ("li-globex-002-1", "Machine Learning Pipeline", 30, 200.00),
                    ("li-globex-002-2", "Cloud Hosting - Monthly", 1, 899.99),
                    ("li-globex-002-3", "Data Engineering", 20, 175.00),
                ],
            },
            {
                "id": "inv-globex-003", "tenant_id": "t-globex-001", "client_id": "c-globex-003",
                "invoice_number": "INV-003", "status": "sent",
                "issue_date": "2026-02-20", "due_date": "2026-03-22", "tax_rate": 0.07,
                "notes": "Legacy system modernization",
                "items": [
                    ("li-globex-003-1", "Code Review & Assessment", 10, 180.00),
                    ("li-globex-003-2", "Database Migration", 12, 175.00),
                    ("li-globex-003-3", "API Integration", 18, 160.00),
                ],
            },
            {
                "id": "inv-globex-004", "tenant_id": "t-globex-001", "client_id": "c-globex-001",
                "invoice_number": "INV-004", "status": "paid",
                "issue_date": "2026-01-15", "due_date": "2026-02-14", "tax_rate": 0.07,
                "notes": "Penetration testing engagement",
                "items": [
                    ("li-globex-004-1", "Penetration Testing", 20, 250.00),
                    ("li-globex-004-2", "Vulnerability Report", 5, 200.00),
                ],
            },
            {
                "id": "inv-globex-005", "tenant_id": "t-globex-001", "client_id": "c-globex-002",
                "invoice_number": "INV-005", "status": "overdue",
                "issue_date": "2026-01-05", "due_date": "2026-02-04", "tax_rate": 0.07,
                "notes": "Training platform development",
                "items": [
                    ("li-globex-005-1", "Web Development Services", 35, 150.00),
                    ("li-globex-005-2", "UI/UX Design", 15, 120.00),
                    ("li-globex-005-3", "Quality Assurance", 10, 130.00),
                ],
            },
        ]

        sort_counter = 0
        for spec in invoice_specs:
            # Calculate amounts from line items
            items_with_amounts = []
            subtotal = 0.0
            for item_id, desc, qty, unit_price in spec["items"]:
                amount = round(qty * unit_price, 2)
                subtotal += amount
                sort_counter += 1
                items_with_amounts.append((item_id, spec["id"], desc, qty, unit_price, amount, sort_counter))

            subtotal = round(subtotal, 2)
            tax_amount = round(subtotal * spec["tax_rate"], 2)
            total = round(subtotal + tax_amount, 2)

            conn.execute(
                "INSERT OR IGNORE INTO invoices "
                "(id, tenant_id, client_id, invoice_number, status, issue_date, due_date, "
                "subtotal, tax_rate, tax_amount, total, notes) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    spec["id"], spec["tenant_id"], spec["client_id"],
                    spec["invoice_number"], spec["status"],
                    spec["issue_date"], spec["due_date"],
                    subtotal, spec["tax_rate"], tax_amount, total,
                    spec["notes"],
                ),
            )

            conn.executemany(
                "INSERT OR IGNORE INTO line_items "
                "(id, invoice_id, description, quantity, unit_price, amount, sort_order) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                items_with_amounts,
            )

        conn.commit()
    finally:
        conn.close()
