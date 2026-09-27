# Specification: Health Endpoint

> This is the live smoke-test specification (see `AGENTS.md` / setup plan, Step 9). It is a separate file from `specs/sample-health-endpoint.md`, which was only a worked example of the template.

- **Spec ID:** `health-endpoint`
- **Status:** Approved

> No implementation may begin until Status = Approved (see `constitution.md`, Principle 1, and `AGENTS.md`, Rule 1).

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
2. The response body is JSON: `{"status": "OK"}`, with `Content-Type: application/json`.
3. The endpoint requires no authentication and no request parameters.
4. Non-`GET` requests to `/health` return HTTP 405 Method Not Allowed.

## Acceptance Criteria (Given/When/Then)

- **Given** the application is running, **When** a client sends `GET /health`, **Then** the response status is `200`.
- **Given** the application is running, **When** a client sends `GET /health`, **Then** the response body is the JSON object `{"status": "OK"}` and the `Content-Type` is `application/json`.
- **Given** the application is running, **When** a client sends `GET /health` with no credentials and no parameters, **Then** the request succeeds with status `200`.
- **Given** the application is running, **When** a client sends `POST /health`, **Then** the response status is `405 Method Not Allowed`.

## Security and Dependencies

- New dependency: `Flask>=3.1` (chosen by human decision on 2026-09-27). Minimal, widely used WSGI framework, sufficient for a single route; its routing returns 405 for unsupported methods by default, keeping the implementation simple (`constitution.md`, Principle 2). To be added to `requirements.txt` only after this spec is Approved.
- Security considerations: endpoint returns no sensitive data and requires no input, so no additional validation or auth is needed. No secrets are involved.

## Open Questions

All resolved by human decision on 2026-09-27:

- **Technology/framework:** Flask.
- **Response format:** JSON `{"status": "OK"}`.
- **Unsupported methods:** return HTTP 405 Method Not Allowed.

## Human Approval

- Approved by: Project maintainer (chat user)
- Date: 2026-09-27

> An agent cannot approve its own specification (see `AGENTS.md`, Section 8).
