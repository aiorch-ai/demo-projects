Build a FastAPI REST API layer on top of the existing contact book data layer in `contact-book/`.

The data layer (db.py, models.py, repository.py) already exists from the previous phase.

Create:
- `contact-book/contacts/api.py` — FastAPI router with endpoints: POST /contacts, GET /contacts, GET /contacts/{id}, PUT /contacts/{id}, DELETE /contacts/{id}, GET /contacts/search?q=
- `contact-book/contacts/main.py` — FastAPI app entry point, mount the router
- `contact-book/tests/test_api.py` — Tests using FastAPI TestClient for all endpoints
