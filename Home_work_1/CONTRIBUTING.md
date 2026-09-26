# Contributing

This project follows a spec-driven workflow: **request → specification → human approval → plan → tasks → implementation → validation → review**. This guide explains how to move through each stage. The underlying reasoning is in `constitution.md`; the enforced rules are in `AGENTS.md`.

## 1. Write and Approve a Specification

1. Copy `specs/TEMPLATE.md` to `specs/<short-slug>.md`.
2. Fill in **Problem**, **Scope / Out of Scope**, **Requirements**, **Acceptance Criteria** (Given/When/Then), and **Security and Dependencies**. See `specs/sample-health-endpoint.md` for a worked example.
3. Record anything unclear under **Open Questions** — do not guess (`constitution.md`, Principle 6).
4. Set `Status: Draft`, then `In Review` once it is ready for a human to read.
5. A human — not the agent who wrote it — reviews it and either:
   - Sets `Status: Approved` and fills in **Human Approval** (name and date), or
   - Sets `Status: Rejected` with a reason, or requests changes.
6. **No implementation begins until `Status: Approved`** (`AGENTS.md`, Rule 1).

## 2. Create a Plan and Tasks

1. Copy `plans/TEMPLATE.md` to `plans/<short-slug>.md` and link the approved specification.
2. Describe the **Approach**, **Affected Files / Modules**, **Sequencing**, **Risks and Rollback**, and **Validation Plan**.
3. Copy `tasks/TEMPLATE.md` to `tasks/<short-slug>.md`, linking the plan and specification.
4. Break the plan into small tasks, each with a clear **Definition of Done**.

## 3. Implement and Test Approved Scope

1. Implement only what is described in the linked plan and specification — nothing more (`constitution.md`, Principle 7).
2. Add a test for every acceptance criterion in the specification (`docs/standards.md`, Testing).
3. Update documentation in the same change: docstrings, `README.md`, or `docs/standards.md` as needed (`constitution.md`, Principle 5).
4. Do not touch a protected path (`AGENTS.md`, Section 6) without approval already recorded in the specification.

## 4. Validate and Submit a Change

1. Run the validation commands from `AGENTS.md`, Section 4:
   ```bash
   python3 -m pytest tests/
   ruff check .
   mypy src
   black --check .
   pip-audit
   ```
2. Fill in `review/change-template.md` completely — every item answered Yes, No, or N/A, with evidence (a link, command output, or file reference).
3. Submit the change referencing its specification, plan, and completed review checklist.
4. A human reviews and approves before the change is merged.

## When to Stop and Ask

Pause and request human input — rather than guessing — whenever you hit a condition listed in `AGENTS.md`, Section 8 (ambiguous requirement, unspecified technology choice, a protected path, an unjustified new dependency, a specification that is not yet Approved, or a validation failure that isn't an obvious, in-scope fix).
