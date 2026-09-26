# Project Constitution

Seven principles that govern how this project is built and changed. Every rule in `AGENTS.md`, `docs/standards.md`, and `CONTRIBUTING.md` exists to serve one of these.

## 1. Specification Before Implementation

No code is written until a specification is approved.
In practice, this means: an agent or contributor drafts a specification from `specs/TEMPLATE.md`, a human sets its `Status` to `Approved`, and only then does implementation begin.

## 2. Simplicity

The simplest design that satisfies the approved requirements is the correct one.
In practice, this means: prefer the standard library and existing modules over new dependencies, avoid speculative abstraction, and justify any added complexity in the specification.

## 3. Verifiable Quality

Every claim of correctness must be demonstrated, not asserted.
In practice, this means: acceptance criteria are written as Given/When/Then, each is covered by an automated test, and `pytest`, `ruff`, `mypy`, and `black --check` all pass before a change is submitted.

## 4. Security by Default

Security is a required property of every change, not an optional add-on.
In practice, this means: no hardcoded secrets, no weakened validation or auth checks, dependencies are justified and audited with `pip-audit`, and protected paths are never touched without explicit approval.

## 5. Documented Decisions

Decisions and their reasoning are recorded where future contributors and agents will find them.
In practice, this means: every module, skill, and non-obvious choice is documented in the relevant file (docstring, `README.md`, or `docs/standards.md`) at the time the change is made, not after.

## 6. Human Control of Ambiguity

When a requirement, scope boundary, or technical choice is unclear, a human decides — the agent does not guess.
In practice, this means: unclear points are recorded as Open Questions in the specification, and implementation is paused until a human resolves them.

## 7. Focused Changes

Each change does one approved thing and nothing more.
In practice, this means: a change stays within the scope defined by its specification, unrelated fixes or refactors are proposed as separate specifications, and reviewers can verify scope with `review/change-template.md`.
