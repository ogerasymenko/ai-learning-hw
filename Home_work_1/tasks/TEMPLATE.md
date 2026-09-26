# Tasks: <Title>

- **Linked Plan:** `plans/<plan-file>.md`
- **Linked Specification:** `specs/<spec-file>.md`

> Each task should be small enough to implement and validate independently. Do not add a task that implements something outside the linked plan's scope.

## Task List

| ID | Description | Depends On | Definition of Done | Status |
|---|---|---|---|---|
| T1 | ... | — | Code written, matching requirement # from the spec | Not Started |
| T2 | ... | T1 | Test added covering the corresponding acceptance criterion | Not Started |
| T3 | ... | T1, T2 | `python3 -m pytest tests/`, `ruff check .`, `mypy src`, `black --check .` pass | Not Started |

Status values: `Not Started`, `In Progress`, `Blocked`, `Done`.

## Blockers

If any task is `Blocked`, record why here and whether it needs human input (see `AGENTS.md`, Section 8).

- ...

## Completion Check

All tasks are `Done`, all acceptance criteria from the linked specification are covered by a passing test, and `review/change-template.md` has been filled in before submission.
