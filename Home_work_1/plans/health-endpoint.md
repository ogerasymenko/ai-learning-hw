# Plan: Health Endpoint

- **Linked Specification:** `specs/health-endpoint.md` (`Status: Approved`)
- **Status:** Done

## Approach

Add a minimal Flask application exposing a single `GET /health` route that returns HTTP 200 with a JSON body `{"status": "OK"}`. Flask returns HTTP 405 automatically for any method not declared on a route, so no extra code is needed to satisfy Requirement 4.

## Affected Files / Modules

| Path | Change |
|---|---|
| `src/health.py` | New — Flask app with the `/health` route |
| `tests/test_health.py` | New — tests covering both acceptance criteria |
| `requirements.txt` | Modified — add `Flask` as a new runtime dependency |

## Sequencing / Dependencies

None. This is a single, self-contained change.

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Sandbox environment cannot install new packages from PyPI (no network access) | Flask is already present in this environment; `pytest`/`ruff`/`mypy`/`black`/`pip-audit` are not — validation for those is run to the extent possible and the gap is disclosed in the review (see `review/health-endpoint-review.md`) |

## Rollback Plan

Revert the commit that adds `src/health.py`, `tests/test_health.py`, and the `Flask` line in `requirements.txt`. No state or migration is involved.

## Validation Plan

- `python3 -m pytest tests/` — both tests in `tests/test_health.py` must pass.
- `ruff check .` / `mypy src` / `black --check .` — no new violations.
- `pip-audit` — check the newly added `Flask` dependency for known vulnerabilities.
