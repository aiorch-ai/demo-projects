# Sample Task — Multi-Tenant Invoice Management API

## Purpose

This is a sample task designed to demonstrate AiOrch's multi-agent orchestration capabilities. It produces a non-trivial FastAPI application with 4 parallel agents working on different concerns — database, API, business logic, and security/testing — that must integrate cleanly.

Ideal for demo videos, onboarding walkthroughs, and verifying a fresh AiOrch installation.

## Focus: Full-Stack Invoice API with FastAPI + SQLite

### Overview

Build a production-grade multi-tenant invoice management API. Four agents work in parallel:

1. **Agent 1 (Database Layer)** — Schema design, SQLite setup, connection management, seed data
2. **Agent 2 (API Layer)** — REST endpoints for all entities, filtering, pagination, error responses
3. **Agent 3 (Business Logic)** — Invoice calculations, status transitions, numbering, PDF generation
4. **Agent 4 (Security & Testing)** — Tenant isolation middleware, API key auth, rate limiting, pytest suite

### Directory Structure

```
sample_tasks/invoice-management-api/
├── README.md                              ← This file
├── 01-database-layer/
│   ├── 01-database-schema-and-setup.md    ← Detailed task spec
│   ├── prompts/
│   │   └── 01-prompt.md                   ← Orchestrator prompt for agent
│   └── migrations/
│       └── 001_initial_schema.sql         ← Reference schema
├── 02-api-layer/
│   ├── 01-rest-endpoints.md
│   └── prompts/
│       └── 01-prompt.md
├── 03-business-logic/
│   ├── 01-invoice-engine.md
│   └── prompts/
│       └── 01-prompt.md
└── 04-security-and-testing/
    ├── 01-security-and-tests.md
    └── prompts/
        └── 01-prompt.md
```

### Execution Order

| Agent | Component | Dependencies | Estimated Time |
|-------|-----------|-------------|----------------|
| Agent 1 | Database layer | None | 3-5 min |
| Agent 2 | API layer | Reads database models (agent 1) | 4-6 min |
| Agent 3 | Business logic | Reads database models (agent 1) | 4-6 min |
| Agent 4 | Security & testing | Reads all modules (agents 1-3) | 5-7 min |

Agents 1-3 can run in parallel. Agent 4 depends on agents 1-3 completing first (it writes integration tests).

### AiOrch Session Configuration

| Field | Value |
|-------|-------|
| Project Root | `/opt/demo-invoice-api` (create empty git repo first) |
| Task Description | See `orchestrator-task.md` below |
| Planning Document | Point to this README or the individual task files |
| Agent Model | `openai:gpt-4o` (fast, good for demo) or `opus` (strongest) |
| Base Branch | `main` |
| Max Parallel Agents | 4 |
| Max Review Rounds | 2 |
| Merge agent branches | Yes |

### Pre-Recording Setup

```bash
# 1. Create the demo project directory
mkdir -p /opt/demo-invoice-api
cd /opt/demo-invoice-api
git init
git checkout -b main
echo "# Invoice Management API" > README.md
git add README.md
git commit -m "Initial commit"

# 2. Create a session in AiOrch pointing to /opt/demo-invoice-api
# 3. Use the task description from the prompt files
# 4. Start the session and record
```

### Success Criteria

- [ ] SQLite database initialises with 4 tables (tenants, clients, invoices, line_items)
- [ ] All CRUD endpoints work for tenants, clients, invoices, and line items
- [ ] Invoices auto-calculate subtotal, tax, and total from line items
- [ ] Invoice numbering follows INV-{YEAR}-{SEQUENCE} format
- [ ] Status transitions are validated (draft → sent → paid; overdue auto-detected)
- [ ] Tenant isolation enforced — tenant A cannot see tenant B's data
- [ ] API key authentication on all endpoints
- [ ] Rate limiting returns 429 when exceeded
- [ ] pytest suite with 20+ tests covering all endpoints
- [ ] requirements.txt, .env.example, and README.md included
- [ ] All agent branches merge cleanly into integration branch
- [ ] GitHub PR created with summary
