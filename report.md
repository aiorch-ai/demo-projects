**Timestamp:** 2026-04-24 20:06:18 (local time)

# Final State

- Updated `contact-book/tests/test_export.py` to fully match the task requirements after review.
- `test_export_csv_with_rows` now asserts the exported CSV header exactly matches `CSV_FIELDS`.
- `test_import_missing_name_raises` now accepts only `ValueError` or `pydantic.ValidationError`, not arbitrary exceptions.

# Validation

- `python -m pytest contact-book/tests/test_export.py` -> `10 passed`
- `python -m py_compile contact-book/tests/test_export.py` -> passed
