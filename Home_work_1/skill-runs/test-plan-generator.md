# Skill Run: test-plan-generator

- **Date:** 2026-09-26
- **Skill:** `skills/test-plan-generator/SKILL.md`

## Input

Specification: `specs/sample-health-endpoint.md` (`Status: Approved`). Relevant sections used as input:

> **Requirements**
> 1. `GET /health` returns HTTP status 200 when the application process is running.
> 2. The response body is JSON: `{"status": "OK"}`.
> 3. The endpoint requires no authentication and no request parameters.
> 4. The endpoint responds in under 100ms under normal load (no external calls).
>
> **Acceptance Criteria (Given/When/Then)**
> - Given the application is running, When a client sends `GET /health`, Then the response status is 200 and the body is `{"status": "OK"}`.
> - Given the application is running, When a client sends `POST /health`, Then the response status is 405 Method Not Allowed.

## Output

```markdown
| Acceptance Criterion | Test Name | Test File | Type | Required/Additional | Notes |
|---|---|---|---|---|---|
| GET /health returns 200 + {"status":"OK"} | test_health_endpoint_returns_200 | tests/test_health.py | Unit | Required | Covers Requirements 1 and 2 |
| POST /health returns 405 | test_health_endpoint_rejects_post | tests/test_health.py | Unit | Required | Covers Requirement 3 (no unintended methods accepted) |
| GET /health requires no auth header | test_health_endpoint_requires_no_auth | tests/test_health.py | Unit | Required | Covers Requirement 3 (no authentication) |
| GET /health responds under 100ms | test_health_endpoint_responds_quickly | tests/test_health.py | Integration | Required | Covers Requirement 4; timing assertion, run outside strict CI resource limits |
| GET /health with unexpected query params | test_health_endpoint_ignores_query_params | tests/test_health.py | Unit | Additional | Edge case not in spec; confirm no error is raised |
| GET /health with unsupported Accept header | test_health_endpoint_ignores_accept_header | tests/test_health.py | Additional | Edge case; spec does not define content negotiation behavior |
```

**Coverage check:** all 4 numbered Requirements and both Acceptance Criteria map to at least one Required test. No Acceptance Criterion was too vague to test, so no Open Question was raised back to the specification.
