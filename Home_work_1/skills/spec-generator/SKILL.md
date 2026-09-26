# Skill: spec-generator

## Purpose and When to Use It

Drafts a specification from a raw, informal request, following `specs/TEMPLATE.md`. Use this skill whenever a new change is requested and no specification exists yet for it. This skill only **drafts**; it never approves its own output (`AGENTS.md`, Section 8).

## Required Inputs

- The raw request (a sentence or short paragraph describing what someone wants).
- `specs/TEMPLATE.md` (structure to follow).
- `docs/standards.md` and `constitution.md` (conventions and principles to respect).
- Any existing related specs or code, to avoid duplicating existing functionality.

## Step-by-Step Instructions

1. Read `specs/TEMPLATE.md` to confirm the current field structure.
2. Restate the request as a **Problem** statement (what and why), without proposing a technology choice unless the request explicitly named one.
3. Draft **Scope** and **Out of Scope** based only on what the request states or clearly implies.
4. Write numbered, testable **Requirements**.
5. Write **Acceptance Criteria** as Given/When/Then, one per requirement where possible.
6. Fill **Security and Dependencies**: name any dependency the requirements clearly require, or write "none identified."
7. For anything the request does not specify — response format, technology stack, edge-case behavior — do **not** guess. Record it under **Open Questions**.
8. Set `Status: Draft`.
9. Save the file as `specs/<short-slug>.md`.

## Stop Conditions

- Stop and leave `Status: Draft` (never set `Approved` or pick a value for **Human Approval**) — approval is always a separate human step.
- If the request requires choosing an unspecified technology or library, do not choose one — record it as an Open Question instead.
- If the request is too vague to produce even a draft Problem statement, stop and ask the human directly rather than producing a speculative spec.

## Output Format

A single markdown file at `specs/<short-slug>.md`, matching the field order and headings of `specs/TEMPLATE.md` exactly.

## Yes/No Quality Checks

- Does the file follow `specs/TEMPLATE.md`'s field order and headings? Yes/No
- Is `Status` set to `Draft` (not `Approved` or `Rejected`)? Yes/No
- Does every Requirement have at least one corresponding Acceptance Criterion? Yes/No
- Is every unclear point recorded under Open Questions rather than resolved by assumption? Yes/No
- Is Security and Dependencies filled in, even if "none identified"? Yes/No

## Example

**Input:** "Add a health endpoint that returns HTTP 200 with status OK."

**Output (excerpt):**
```markdown
- **Status:** Draft

## Problem
Operators have no way to check whether the service is running.

## Requirements
1. GET /health returns HTTP 200 when the process is running.

## Acceptance Criteria (Given/When/Then)
- Given the app is running, When a client sends GET /health, Then the response status is 200.

## Open Questions
- The request does not specify a response body format. Should it be JSON, plain text, or empty? Confirm before implementation.
```
