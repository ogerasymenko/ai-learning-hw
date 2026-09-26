# Skill Run: spec-generator

- **Date:** 2026-09-26
- **Skill:** `skills/spec-generator/SKILL.md`

## Input

> Add a `/version` endpoint that returns the running application's version string.

## Output

Saved as `specs/version-endpoint.md` (draft — not yet reviewed by a human):

```markdown
# Specification: Version Endpoint

- **Spec ID:** `version-endpoint`
- **Status:** Draft

## Problem

Operators and client applications have no way to query which version of the service is currently deployed, which makes it hard to confirm a rollout or diagnose version-specific issues.

## Scope

### In Scope
- A single HTTP `GET /version` endpoint that returns the application's version string.

### Out of Scope
- Build metadata (commit hash, build date).
- Version negotiation or compatibility checks.
- Authentication on this endpoint.

## Requirements

1. `GET /version` returns HTTP status 200 when the application process is running.
2. The response includes the application's current version string.
3. The endpoint requires no authentication and no request parameters.

## Acceptance Criteria (Given/When/Then)

- **Given** the application is running, **When** a client sends `GET /version`, **Then** the response status is `200` and the body includes the version string.

## Security and Dependencies

- No new dependency identified; version reporting can likely use the existing web framework already approved for `specs/sample-health-endpoint.md`, pending confirmation (see Open Questions).
- Security considerations: none identified — the version string is not sensitive.

## Open Questions

- Where does the version string come from — a hardcoded constant, `pyproject.toml` package metadata, or an environment variable set at build time? The request does not say.
- What is the exact response format — plain text, or JSON such as `{"version": "..."}`? The request does not say.

## Human Approval

- Approved by:
- Date:
```

## Notes

Per the skill's stop conditions, both the version-source mechanism and the response format were left unresolved as **Open Questions** rather than guessed, and `Status` was set to `Draft` — this skill never sets `Approved` or fills in `Human Approval` itself.
