# Tasks: Health Endpoint

- **Linked Plan:** `plans/health-endpoint.md`
- **Linked Specification:** `specs/health-endpoint.md`

## Task List

| ID | Description | Depends On | Definition of Done | Status |
|---|---|---|---|---|
| T1 | Add `Flask` to `requirements.txt` | — | Line present, matches the version approved in the spec's Security and Dependencies section | Done |
| T2 | Implement `src/health.py` with `GET /health` returning `{"status": "OK"}` | T1 | Matches Requirements 1–4 of the spec | Done |
| T3 | Add `tests/test_health.py` covering both acceptance criteria | T2 | One test per Given/When/Then in the spec | Done |
| T4 | Run validation (`pytest`, `ruff`, `mypy`, `black`, `pip-audit`) | T2, T3 | Results recorded in `review/health-endpoint-review.md`, including any tool that could not run | Done |
| T5 | Complete `review/change-template.md` for this change | T4 | All 8 rows answered with evidence | Done |

## Blockers

None remaining. `pytest`, `ruff`, `mypy`, `black`, and `pip-audit` were run by a human outside this sandbox (which has no network access to PyPI) and all pass — see `review/health-endpoint-review.md` for the full record, including the one `mypy` error that was found and fixed along the way.

## Completion Check

All tasks are `Done`. Acceptance criteria are covered by tests in `tests/test_health.py`. `review/change-template.md` has been filled in (`review/health-endpoint-review.md`), disclosing the one environment limitation above.
