# AGENTS.md

Canonical instructions for any AI coding agent (e.g. Claude Code) working in this repository. Platform-neutral: applies regardless of which agent or tool is used.

## 1. Project Purpose

This repository is a **spec-driven development foundation** for a Python project. Its purpose, before any feature code is written, is to establish:
- A documented workflow for how change happens (specification → approval → plan → tasks → implementation → validation → review).
- Reusable AI skills that automate parts of that workflow.
- Clear rules on scope, security, and when the agent must stop and ask a human.

No application feature exists yet. The only code allowed before human approval is the single smoke-test change described in `CONTRIBUTING.md`.

## 2. Mandatory Workflow

Every time you create, modify, or remove a Python module, package, or dependency, follow this workflow.

### 2.1 Understand the Change

Before writing code:

- Inspect the existing package/module structure under `src/`.
- Read the relevant specification, plan, and task (do not implement without an Approved spec — see Section 8).
- Check existing naming conventions in `docs/standards.md`.
- Check required docstring, typing, and logging conventions in `docs/standards.md`.
- Check security requirements in `docs/standards.md` and Section 7 of this file.
- Reuse existing modules and functions where possible.
- Do not create duplicate functionality.

### 2.2 Update Documentation

After creating or modifying code, ALWAYS update the relevant documentation. Do not leave documentation outdated after a change.

Documentation must describe:
- What the module/function does.
- Required inputs and parameters (with types).
- Important configuration or environment variables.
- Dependencies (and why each is needed).
- Outputs / return values.
- Security considerations.
- Example usage.

If the module has a `README.md` or module-level docstring, update it.

Example: if you create or modify

`src/<package>/<module>.py`

you must also check and update:
- The module's docstring.
- `README.md`, if it documents this module's usage.
- `docs/standards.md`, if the change introduces a new convention.

### 2.3 Complete the Change

Do not consider a change complete until validation succeeds (Section 4) and the review checklist (`review/change-template.md`) is fully answered.

## 3. Folder Map

| Path | Contents |
|---|---|
| `AGENTS.md` | This file — agent instructions (you are here). |
| `README.md` | Human-facing project overview. |
| `CONTRIBUTING.md` | Step-by-step contribution process. |
| `constitution.md` | Seven governing principles for the project. |
| `docs/standards.md` | Naming, submission, documentation, dependency, security, and testing conventions. |
| `specs/TEMPLATE.md` | Specification template. |
| `specs/sample-health-endpoint.md` | Worked example of a filled-in specification. |
| `plans/TEMPLATE.md` | Plan template (used after a spec is approved). |
| `tasks/TEMPLATE.md` | Task breakdown template. |
| `skills/<skill-name>/SKILL.md` | Reusable agent skills (`spec-generator`, `pr-reviewer`, `test-plan-generator`). |
| `skill-runs/<skill-name>.md` | Recorded input/output of each skill's first real run. |
| `review/change-template.md` | Change-review checklist (Yes/No/N/A + evidence). |
| `src/` | Application source code. **Empty until the approved smoke test.** |
| `tests/` | Automated tests. **Empty until the approved smoke test.** |

## 4. Validation Commands

Run these before submitting any change. All must pass. Do not consider a module change complete until validation succeeds, and record the validation status (command + result) as evidence in the review checklist.

```bash
# Tests
python3 -m pytest tests/

# Linting
ruff check .

# Type checking
mypy src

# Formatting check
black --check .

# Dependency / vulnerability audit
pip-audit
```

If a command is not yet applicable (e.g. `src/` is empty), the agent notes this explicitly in the change review rather than skipping validation silently.

## 5. Governance Documents

- [Constitution](constitution.md) — seven guiding principles.
- [Contributing guide](CONTRIBUTING.md) — the end-to-end process.
- [Standards](docs/standards.md) — conventions and examples.
- [Specification template](specs/TEMPLATE.md) / [sample spec](specs/sample-health-endpoint.md)
- [Plan template](plans/TEMPLATE.md)
- [Task template](tasks/TEMPLATE.md)
- [Change review template](review/change-template.md)
- Skills: [`spec-generator`](skills/spec-generator/SKILL.md), [`pr-reviewer`](skills/pr-reviewer/SKILL.md), [`test-plan-generator`](skills/test-plan-generator/SKILL.md)

## 6. Protected Paths

The agent must **never modify these without explicit human approval**, even if a task seems to require it:

- `AGENTS.md` (this file)
- `constitution.md`
- `docs/standards.md`
- `review/change-template.md`
- `.github/` (CI/CD workflows, if present)
- Any dependency lock file (e.g. `requirements.txt`, `poetry.lock`) — edits require a documented, justified reason in the spec.
- Any secrets, credentials, or environment configuration files (e.g. `.env`, `*.pem`, `*.key`).

## 7. Secret-Handling Rules

- Never read, print, log, or commit secret values (API keys, tokens, passwords, credentials).
- Never hardcode secrets in source, tests, specs, or skill runs — use placeholders (e.g. `<API_KEY>`) in documentation.
- If a task appears to require a new secret or credential, stop and record it as an **Open Question** in the relevant spec; do not generate or invent one.
- Never weaken existing security controls (auth checks, input validation, dependency pinning) to make a task easier.

## 8. Conditions Requiring Human Input

Stop and ask — do not guess — when:
- A requirement, acceptance criterion, or scope boundary is ambiguous.
- A task would require choosing an unspecified technology, library, or framework.
- A task would touch a protected path.
- A task would add a new dependency not already justified in an approved spec.
- No specification exists yet, or the existing specification's `Status` is not `Approved`. An agent cannot approve its own specification (Section 9, Rule 6).
- Validation fails and the fix is not a small, obvious correction within approved scope.

## 9. Required Rules

1. **No feature implementation without an approved specification.** Draft specs are for review, not for building against.
2. **Run applicable validation before submitting any change**, and report the actual command output as evidence.
3. **Never expose secrets or weaken security and tests** to make a change pass.
4. **Never modify protected paths without explicit approval** recorded in the relevant specification or review.
5. **If requirements are unclear, stop and ask a human.** Do not guess, assume, or fill gaps silently.
6. **An agent never approves its own work.** Only a human may set a specification's `Status` to `Approved` or fill in its Human Approval section. An agent may draft a spec and set it to `Draft` or `In Review`, but must wait for the human's explicit approval in chat or in the spec itself. This also applies to a specification the agent drafted or edited.
