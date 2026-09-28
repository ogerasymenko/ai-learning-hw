# Specification: Health Endpoint

> This is the live smoke-test specification (see `AGENTS.md` / setup plan, Step 9). It is a separate file from `specs/sample-health-endpoint.md`, which was only a worked example of the template.

- **Spec ID:** `health-endpoint`
- **Status:** Draft

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
2. The response body indicates status "OK" (exact format pending — see Open Questions).
3. The endpoint requires no authentication and no request parameters.

## Acceptance Criteria (Given/When/Then)

- **Given** the application is running, **When** a client sends `GET /health`, **Then** the response status is `200`.
- **Given** the application is running, **When** a client sends `GET /health`, **Then** the response body indicates status "OK" in the format agreed under Open Questions.
- **Given** the application is running, **When** a client sends `GET /health` with no credentials and no parameters, **Then** the request succeeds with status `200`.

## Security and Dependencies

- New dependencies: none identified until the framework question is resolved. Any framework chosen must be named here with version and justification, and added to `requirements.txt` only after approval.
- Security considerations: endpoint returns no sensitive data and requires no input, so no additional validation or auth is needed. No secrets are involved.

## Open Questions

- **Technology/framework:** Which technology or framework should serve the endpoint (e.g. Flask, FastAPI, Python standard library `http.server`)? This determines whether a new dependency is added.
- **Response format:** What response body format is required — JSON (e.g. `{"status": "OK"}`), plain text (`OK`), or another format? This also determines the `Content-Type` header.
- **Unsupported methods:** How should non-`GET` requests to `/health` (e.g. `POST`) be handled — HTTP 405 Method Not Allowed, or left to the framework default?

## Human Approval

- Approved by: `<name>`
- Date: `<YYYY-MM-DD>`

> An agent cannot approve its own specification (see `AGENTS.md`, Section 8).
