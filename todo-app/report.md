**Timestamp:** 2026-04-24 12:07:41 (local time)

Final state:
- `todo/cli.py` now traps `argparse` parser exits and returns a non-zero `int` from `main(argv=None)` instead of propagating `SystemExit` on invalid CLI input.
- `tests/test_cli.py` now asserts the return-code contract and runs against Agent 1's `todo.db`, `todo.models`, `todo.service`, and fixture module at runtime instead of carrying copied core files in this branch.
- Branch scope is reduced to the CLI presentation layer files only: `todo/cli.py`, `todo/display.py`, and `tests/test_cli.py`.

Verification:
- `python -m pytest tests/test_cli.py`
- `python -m py_compile todo/cli.py todo/display.py tests/test_cli.py`
