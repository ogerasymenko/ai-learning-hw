# Specification: Health Endpoint (Sample)

> **This is a worked example**, included to show how `specs/TEMPLATE.md` should be filled in. It is not the live smoke-test specification — the smoke test (Section 9 of the setup plan) will produce its own specification from scratch, drafted by the agent from a one-line request.

- **Spec ID:** `sample-health-endpoint`
- **Status:** Approved

## Problem

Operators and orchestration tools (e.g. a load balancer or Kubernetes) have no way to check whether the running service is up and responding. We need a lightweight endpoint that reports basic liveness.

## Scope

### In Scope
- A single HTTP `GET /health` endpoint.
- Returns HTTP 200 with a JSON body `{"status": "OK"}` when the process is running.

### Out of Scope
- Deep health checks (database connectivity, downstream dependencies).
- Authentication on this endpoint.
- Metrics or monitoring integration.

## Requirements

1. `GET /health` returns HTTP status 200 when the application process is running.
2. The response body is JSON: `{"status": "OK"}`.
3. The endpoint requires no authentication and no request parameters.
4. The endpoint responds in under 100ms under normal load (no external calls).

## Acceptance Criteria (Given/When/Then)

- **Given** the application is running, **When** a client sends `GET /health`, **Then** the response status is `200` and the body is `{"status": "OK"}`.
- **Given** the application is running, **When** a client sends `POST /health`, **Then** the response status is `405 Method Not Allowed` (only `GET` is supported).

## Security and Dependencies

- New dependency: `fastapi==0.115.0` — a minimal, actively maintained web framework already permitted for HTTP endpoints; chosen over building routing by hand to keep the implementation simple (Principle 2, Simplicity).
- Security considerations: endpoint returns no sensitive data and requires no input, so no additional validation or auth is needed. No secrets are involved.

## Open Questions

- None. (If this were a real, non-sample spec with open questions, implementation would not begin until they are resolved — see `AGENTS.md`, Section 8.)

## Human Approval

- Approved by: `Jane Doe (example reviewer)`
- Date: `2026-09-20`
