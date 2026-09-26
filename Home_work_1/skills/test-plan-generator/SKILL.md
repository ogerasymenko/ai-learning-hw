# Skill: test-plan-generator

## Purpose and When to Use It

Maps every Acceptance Criterion in an approved specification to concrete, named automated tests, before or during implementation. Use this skill right after a specification becomes `Approved`, as part of building `tasks/<slug>.md`, to make coverage verifiable up front (`constitution.md`, Principle 3, Verifiable Quality).

## Required Inputs

- The approved specification (`Requirements` and `Acceptance Criteria` sections).
- `docs/standards.md` (Testing conventions, naming conventions).
- The existing `tests/` structure, to match naming and avoid duplicate test files.

## Step-by-Step Instructions

1. Confirm the specification's `Status` is `Approved`. If not, stop (see Stop Conditions).
2. List every Acceptance Criterion from the specification.
3. For each criterion, define one or more test cases: a descriptive test function name following `tests/test_<module>.py::test_<behavior>`, the test type (unit or integration), inputs, and expected output.
4. Mark each of these as **Required** — they trace directly to an acceptance criterion.
5. If the requirements imply reasonable edge cases not explicitly covered by an acceptance criterion (e.g. invalid input, unsupported HTTP method), add them as **Additional** test cases, clearly separated from Required ones.
6. Verify every Acceptance Criterion maps to at least one Required test.
7. Output the mapping as a markdown table.

## Stop Conditions

- If the specification's `Status` is not `Approved`, stop and report this — do not generate a test plan against an unapproved spec.
- If an Acceptance Criterion is too vague to derive a concrete expected value (e.g. no defined response body), do not invent one. Record it as an Open Question back to the specification rather than guessing the expected behavior.

## Output Format

A markdown table with columns: `Acceptance Criterion | Test Name | Test File | Type | Required/Additional | Notes`.

## Yes/No Quality Checks

- Does every Acceptance Criterion map to at least one Required test? Yes/No
- Do all test names follow the `tests/test_<module>.py::test_<behavior>` convention from `docs/standards.md`? Yes/No
- Are Additional (edge-case) tests clearly separated from Required tests? Yes/No
- Is any criterion too vague to test flagged as an Open Question instead of resolved by assumption? Yes/No

## Example

**Input:** `specs/sample-health-endpoint.md` (Approved), with two acceptance criteria (GET returns 200/OK; POST returns 405).

**Output:**
```markdown
| Acceptance Criterion | Test Name | Test File | Type | Required/Additional | Notes |
|---|---|---|---|---|---|
| GET /health returns 200 + {"status":"OK"} | test_health_endpoint_returns_200 | tests/test_health.py | Unit | Required | — |
| POST /health returns 405 | test_health_endpoint_rejects_post | tests/test_health.py | Unit | Required | — |
| GET /health with query params | test_health_endpoint_ignores_query_params | tests/test_health.py | Unit | Additional | Edge case not in spec; confirm no error is raised |
```
