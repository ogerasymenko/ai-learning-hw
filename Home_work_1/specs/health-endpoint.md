# Specification: Health Endpoint

> This is the live smoke-test specification (see `AGENTS.md` / setup plan, Step 9). It is a separate file from `specs/sample-health-endpoint.md`, which was only a worked example of the template.

- **Spec ID:** `health-endpoint`
- **Status:** Approved

## Problem

Operators and orchestration tools (e.g. a load balancer or container orchestrator) have no way to check whether the running service is up and responding.

## Scope

### In Scope
- A single HTTP `GET /health` endpoint that returns HTTP 200 with a body indicating status "OK" when the process is running.

### Out of Scope
- Deep health checks (database connectivity, downstream dependencies).
- Authentication on this endpoint.
- Metrics or monitoring integration.

## Requirements

1. `GET /health` returns HTTP status 200 when the application process is running.
2. The response body is JSON: `{"status": "OK"}`.
3. The endpoint requires no authentication and no request parameters.
4. Non-`GET` requests to `/health` return HTTP 405.

## Acceptance Criteria (Given/When/Then)

- **Given** the application is running, **When** a client sends `GET /health`, **Then** the response status is `200` and the body is `{"status": "OK"}`.
- **Given** the application is running, **When** a client sends `POST /health`, **Then** the response status is `405 Method Not Allowed`.

## Security and Dependencies

- New dependency: `Flask` (chosen by human decision on 2026-09-26). Minimal, widely used WSGI framework, sufficient for a single route; keeps the implementation simple (`constitution.md`, Principle 2).
- Security considerations: endpoint returns no sensitive data and requires no input, so no additional validation or auth is needed. No secrets are involved.

## Open Questions

- None. Resolved by human decision on 2026-09-26: framework = Flask; response format = JSON `{"status": "OK"}`.

## Human Approval

- Approved by: Project maintainer (chat user)
- Date: 2026-09-26
