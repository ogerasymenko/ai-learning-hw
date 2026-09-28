# Tasks: Health Endpoint

- **Linked Plan:** `plans/health-endpoint.md`
- **Linked Specification:** `specs/health-endpoint.md` (`Status: Draft`)

> Each task should be small enough to implement and validate independently. Do not add a task that implements something outside the linked plan's scope.

## Task List

| ID | Description | Depends On | Definition of Done | Status |
|---|---|---|---|---|
| T1 | Add the approved dependency (if any) to `requirements.txt` | — | Line present, matches the version approved in the spec's Security and Dependencies section | Blocked |
| T2 | Implement `src/health.py` with `GET /health` | T1 | Matches all Requirements of the approved spec | Blocked |
| T3 | Add `tests/test_health.py` covering the acceptance criteria | T2 | One test per Given/When/Then in the spec | Blocked |
| T4 | Run validation (`pytest`, `ruff`, `mypy`, `black`, `pip-audit`) | T2, T3 | Results recorded in `review/health-endpoint-review.md` | Not Started |
| T5 | Complete `review/change-template.md` for this change | T4 | All 8 rows answered with evidence | Not Started |

Status values: `Not Started`, `In Progress`, `Blocked`, `Done`.

## Blockers

- `specs/health-endpoint.md` is `Draft` with unresolved Open Questions (framework, response format, unsupported-method handling). Needs human decisions and approval (`AGENTS.md`, Section 8).

## Completion Check

All tasks are `Done`, all acceptance criteria from the linked specification are covered by a passing test, and `review/change-template.md` has been filled in before submission.
