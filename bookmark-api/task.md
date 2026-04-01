# Sample Task — Bookmark Manager API (Single Session)

## Purpose

This is a sample task designed to test AiOrch's **session** workflow (not pipeline). It produces a clean FastAPI application with 3 parallel agents working on different parts of a bookmark management API. Simpler than the invoice task — completes in 5-8 minutes, ideal for verifying a fresh installation or quick demos.

## AiOrch Session Configuration

| Field | Value |
|-------|-------|
| Project Root | `/opt/demo-bookmark-api` (create empty git repo first) |
| Task Description | Copy from `prompt.md` |
| Planning Document | Point to this file |
| Agent Model | `openai:gpt-4o` or `opus` |
| Base Branch | `main` |
| Max Parallel Agents | 3 |
| Max Review Rounds | 2 |
| Merge agent branches | Yes |

## Pre-Recording Setup

```bash
mkdir -p /opt/demo-bookmark-api
cd /opt/demo-bookmark-api
git init
git checkout -b main
echo "# Bookmark Manager API" > README.md
git add README.md
git commit -m "Initial commit"
```

## What Gets Built

A personal bookmark manager API where users can save, tag, search, and organise web bookmarks into collections. Three agents work in parallel:

| Agent | Focus | Files |
|-------|-------|-------|
| Agent 1 | Database + models + seed data | `app/database.py`, `app/models.py`, `app/seed.py`, `requirements.txt`, `.env.example` |
| Agent 2 | REST endpoints + main app | `app/main.py`, `app/routes/bookmarks.py`, `app/routes/collections.py`, `app/routes/tags.py` |
| Agent 3 | Search, import/export, tests, README | `app/services/search.py`, `app/services/import_export.py`, `tests/test_api.py`, `README.md` |

## Success Criteria

- [ ] SQLite database with 4 tables: bookmarks, collections, tags, bookmark_tags
- [ ] Full CRUD for bookmarks, collections, and tags
- [ ] Bookmarks support multiple tags (many-to-many)
- [ ] Bookmarks can be assigned to a collection
- [ ] Full-text search across bookmark title, URL, and description
- [ ] Import/export bookmarks as JSON
- [ ] 15+ pytest tests pass
- [ ] README with quick start and endpoint docs
- [ ] All agent branches merge cleanly
