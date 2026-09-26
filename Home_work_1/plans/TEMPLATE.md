# Plan: <Title>

- **Linked Specification:** `specs/<spec-file>.md` (must have `Status: Approved`)
- **Status:** Draft | Ready | In Progress | Done

> A plan translates an approved specification into a concrete technical approach. It does not re-argue scope — anything not in the linked specification is out of scope for this plan (see `constitution.md`, Principle 7, Focused Changes).

## Approach

Short description (a few sentences) of how the requirements will be met: overall design, key modules involved, and any notable technical decisions.

## Affected Files / Modules

| Path | Change |
|---|---|
| `src/<module>.py` | New / Modified — one-line description |
| `tests/test_<module>.py` | New / Modified — one-line description |

## Sequencing / Dependencies

Does this plan depend on other plans, external services, or must steps happen in a specific order? List them, or write "None."

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| ... | ... |

## Rollback Plan

How to revert this change if it causes a problem after submission (e.g. revert commit, feature flag, no state migration involved).

## Validation Plan

Which commands from `AGENTS.md` Section 4 apply, and what "pass" looks like for this specific change.

- `python3 -m pytest tests/` — all new tests in the Affected Files table pass.
- `ruff check .` / `mypy src` / `black --check .` — no new violations.
- `pip-audit` — only if a new dependency was added.
