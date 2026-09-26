# Standards

Conventions for this Python project. Every convention below is enforced by validation commands in `AGENTS.md` and checked in `review/change-template.md`.

## Naming

- Modules and packages: `snake_case`, short, one clear responsibility (e.g. `health_check.py`, not `helpers.py`).
- Functions and variables: `snake_case`, descriptive, no abbreviations that hide meaning.
- Classes: `PascalCase`. Constants: `UPPER_SNAKE_CASE`.
- Test files mirror the module they test: `tests/test_<module>.py`.

**Good:**
```python
def get_user_by_id(user_id: int) -> User: ...
```

**Bad:**
```python
def gub(x): ...  # unclear abbreviation, no type hints
```

## Change Submission

- Every change references its approved specification (e.g. in the PR description: `Spec: specs/sample-health-endpoint.md`).
- One change = one approved scope. Unrelated fixes go in a separate specification and change.
- Commit messages describe *what* and *why*, not just *what*.

**Good:**
```
Add /health endpoint returning 200 OK

Implements specs/sample-health-endpoint.md (Approved 2026-09-20).
```

**Bad:**
```
fix stuff
```

## Documentation

- Every public function, class, and module has a docstring describing purpose, parameters, and return value.
- `README.md` is updated whenever a change affects how the project is used or run.
- Documentation is updated in the same change as the code it describes, not in a follow-up.

**Good:**
```python
def get_user_by_id(user_id: int) -> User:
    """Return the User matching user_id.

    Raises:
        UserNotFoundError: if no user with this id exists.
    """
```

**Bad:**
```python
def get_user_by_id(user_id):
    # no docstring, no type hints
    ...
```

## Dependencies

- Every new dependency is named and justified in the specification's "Security and Dependencies" section before it is added.
- Dependencies are pinned to an exact or minimum-compatible version in `requirements.txt` (or `pyproject.toml`).
- Prefer the standard library over a new dependency when it can do the job.

**Good:**
```
# requirements.txt
fastapi==0.115.0  # justified in specs/sample-health-endpoint.md: HTTP framework for the health endpoint
```

**Bad:**
```
# requirements.txt
fastapi
some-random-package  # added without a spec reference
```

## Security

- No secrets, tokens, or credentials in source code, tests, or documentation — use environment variables or a secrets manager, referenced by placeholder.
- All external input is validated before use.
- Dependencies are checked with `pip-audit` before submission; known vulnerabilities block the change.

**Good:**
```python
import os
API_KEY = os.environ["API_KEY"]
```

**Bad:**
```python
API_KEY = "sk-live-abc123..."  # hardcoded secret
```

## Testing

- Every acceptance criterion in an approved specification has at least one corresponding automated test.
- Tests follow Arrange-Act-Assert and test behavior, not implementation details.
- `pytest` must pass, and new code must not lower overall coverage.

**Good:**
```python
def test_health_endpoint_returns_200():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "OK"}
```

**Bad:**
```python
def test_health():
    assert True  # does not test actual behavior
```
