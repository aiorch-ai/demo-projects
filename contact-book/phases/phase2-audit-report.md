**Timestamp:** 2026-04-24 19:43:00

# Phase 2 API Audit Report

## Scope
Compare the delivered implementation on branch `orch/29a6dadb-audit-session-verify-that/agent-3` (merge-base `9d3af71` + agent-1 merge `f123030` + agent-2 tests `47a16dd`) against the requirements in `phase2-api.md`.

## 1. Requirement-by-Requirement Checklist

Spec deliverable: `contact-book/contacts/api.py` — FastAPI router with six endpoints.

| # | Spec Requirement | Implementation | File:Line | Status |
|---|------------------|----------------|-----------|--------|
| 1 | `POST /contacts` | `@router.post("", response_model=Contact, status_code=201)` handler `create_contact` accepts `ContactCreate`, calls `repository.create`, returns 201 with created contact. | `contacts/api.py:16-18` | ✅ PASS |
| 2 | `GET /contacts` | `@router.get("", response_model=list[Contact])` handler `get_contacts` calls `repository.list_all`, returns ordered list. | `contacts/api.py:21-23` | ✅ PASS |
| 3 | `GET /contacts/{id}` | `@router.get("/{contact_id}", response_model=Contact)` handler `get_contact` calls `repository.get_by_id`, raises `HTTPException(404)` on miss. | `contacts/api.py:26-31` | ✅ PASS |
| 4 | `PUT /contacts/{id}` | `@router.put("/{contact_id}", response_model=Contact)` handler `update_contact` accepts `ContactUpdate`, calls `repository.update`, raises `HTTPException(404)` on miss. Supports partial updates via `exclude_unset=True`. | `contacts/api.py:34-39` | ✅ PASS |
| 5 | `DELETE /contacts/{id}` | `@router.delete("/{contact_id}", status_code=204)` handler `delete_contact` calls `repository.delete`, raises `HTTPException(404)` on miss, returns empty `Response` with 204. | `contacts/api.py:42-46` | ✅ PASS |
| 6 | `GET /contacts/search?q=` | `@router.get("/search", response_model=list[Contact])` handler `search_contacts` requires query param `q: str`, calls `repository.search_by_name`. Declared **before** `/{contact_id}` so path matching is unambiguous. | `contacts/api.py:11-13` | ✅ PASS |

### Router Configuration
- Router prefix and tags: `contacts/api.py:8` — `APIRouter(prefix="/contacts", tags=["contacts"])`
- Path ordering verified via `app.routes` dump: `/contacts/search` precedes `/contacts/{contact_id}`.

---

## 2. FastAPI App Entry Point Verification

Spec deliverable: `contact-book/contacts/main.py` — FastAPI app entry point, mount the router.

| Check | Detail | File:Line | Status |
|-------|--------|-----------|--------|
| FastAPI instantiation | `app = FastAPI(title="Contact Book API", version="1.0.0", lifespan=lifespan)` | `contacts/main.py:17` | ✅ PASS |
| Lifespan/startup | `@asynccontextmanager` `lifespan` calls `init_db()` once on startup. | `contacts/main.py:11-14` | ✅ PASS |
| Router mount | `app.include_router(router)` mounts the `contacts.api.router` under `/contacts`. | `contacts/main.py:19` | ✅ PASS |
| Import chain | `from contacts.api import router` resolves cleanly; `from contacts.db import init_db` resolves cleanly. | `contacts/main.py:7-8` | ✅ PASS |

---

## 3. Test Enumeration — `contact-book/tests/test_api.py`

Total: **18 test functions** (12 original + 6 added by agent-2).

### Original 12 tests

| # | Function | Description |
|---|----------|-------------|
| 1 | `test_create_contact` | POST full payload → 201, all fields persisted, id/timestamps generated. |
| 2 | `test_create_contact_missing_name` | POST missing required `name` → 422 validation error. |
| 3 | `test_list_contacts_empty` | GET /contacts with no data → 200 and `[]`. |
| 4 | `test_list_contacts_sorted` | Create 3 contacts out of order; GET returns name-ASC sorted list. |
| 5 | `test_get_contact_hit` | GET existing contact → 200 with matching data. |
| 6 | `test_get_contact_miss` | GET nonexistent id → 404. |
| 7 | `test_update_contact_partial` | PUT partial payload (email only) → 200, untouched fields unchanged. |
| 8 | `test_update_contact_missing` | PUT to nonexistent id → 404. |
| 9 | `test_delete_contact_existing` | DELETE existing → 204; subsequent GET → 404. |
| 10 | `test_delete_contact_missing` | DELETE nonexistent → 404. |
| 11 | `test_search_contacts_case_insensitive` | Search substring case-insensitively; returns matching subset. |
| 12 | `test_search_contacts_empty_query` | Search with `q=""` → 200 and `[]`. |

### Added 6 tests (agent-2)

| # | Function | Description |
|---|----------|-------------|
| 13 | `test_search_missing_q_param` | GET /contacts/search without `q` → 422 (FastAPI required param). |
| 14 | `test_search_no_matches` | Search string that matches nothing → 200 and `[]`. |
| 15 | `test_update_empty_body` | PUT `{}` to existing contact → 200, only `updated_at` changes, `created_at` and all other fields unchanged. |
| 16 | `test_update_invalid_field_type` | PUT with `name` as integer → 422 validation error. |
| 17 | `test_create_minimal_payload` | POST only `{"name": "..."}` → 201, optional fields are `null`. |
| 18 | `test_update_timestamps` | After PUT, `updated_at` > `created_at` (uses `time.sleep(1)` for SQLite second precision). |

---

## 4. Deviations / Quality Issues

Citing risks from the pre-analysis report §7.

### 4.1 Duplicate Commits
- **Observation:** The integrated branch history contains duplicate commits for `api.py`, `main.py`, and `requirements.txt` (agent-2 produced `c8269f2` / `d094ea5` / `800b689`; agent-4 later produced byte-identical `b25cf2c` / `acc2f2c` / `212dcf3`).
- **Impact:** Low. Content is identical; history is slightly noisy. Merge was done `--no-ff` preserving all commits.
- **Status:** Documented, non-blocking.

### 4.2 `sys.modules` Purge Fragility
- **Observation:** `tests/conftest.py` (`client` fixture, lines 37-39) and `db` fixture (lines 17-19) both purge `contacts.*` from `sys.modules` before importing `contacts.db` and `contacts.main`. This prevents stale `DATABASE_URL` from leaking across tests.
- **Impact:** Medium fragility. If any future module performs module-level DB initialization, the purge ordering may no longer be sufficient.
- **Status:** Works for current codebase; flag for Phase 3 test-hardening.

### 4.3 PUT `{}` `total_changes` Latent Bug
- **Observation:** In `contacts/repository.py:66-74`, when `fields` is empty (`PUT {}`), the code uses `conn.total_changes` (cumulative per connection) instead of `cur.rowcount` to determine whether the row existed. Because `get_db()` commits on success, prior operations in the same connection can inflate `total_changes`, potentially masking a missing row.
- **Repro path:** `test_update_empty_body` (test_api.py:133-155) currently passes because the isolated test database has no prior writes in that connection scope, but the pattern is fragile.
- **Status:** **Latent bug — documented, not fixed** (out of phase-2 scope per instructions).

### 4.4 Trailing-Slash 307 Behavior
- **Observation:** Router paths use `""` (bare `/contacts`) and `"/search"`. A request to `/contacts/` will receive a FastAPI default 307 redirect to `/contacts`. The spec is silent on trailing-slash policy.
- **Impact:** Low. Standard FastAPI behavior; clients following redirects are unaffected.
- **Status:** Acceptable for phase-2 scope.

### 4.5 Additional Minor Notes
- No auth, CORS, or rate limiting — explicitly out of phase-2 scope.
- No pagination on `GET /contacts` — spec is silent, acceptable for demo scope.
- Validation remains `str | None` with no `EmailStr` or length constraints — consistent with Phase 1 models.

---

## 5. Final Verdict

**Verdict: PASS-WITH-NOTES**

All six required endpoints are implemented, correctly mounted, and fully tested. The 18 TestClient tests all pass. The single notable reservation is the documented latent bug in `repository.update` when handling an empty body (`PUT {}`), which uses `conn.total_changes` instead of `cur.rowcount`. This does not affect current test outcomes but should be hardened in Phase 3.

### Pytest Summary
```
============================== 55 passed in 4.65s ==============================
```

(55 tests total: 18 API tests + 37 pre-existing data-layer tests, all passing.)
