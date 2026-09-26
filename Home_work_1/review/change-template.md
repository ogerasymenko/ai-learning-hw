# Change Review Checklist

Fill in every item below before submitting a change. Every answer must be **Yes**, **No**, or **Not Applicable**, together with **evidence** — a link, a command's output, or a file reference. Do not leave an item blank.

This same checklist is used by the `pr-reviewer` skill (`skills/pr-reviewer/SKILL.md`); its output should match this structure exactly.

- **Change:** `<short description or link to PR>`
- **Linked Specification:** `specs/<file>.md` (must be `Status: Approved`)
- **Linked Plan / Tasks:** `plans/<file>.md`, `tasks/<file>.md`

| # | Question | Answer (Yes / No / N/A) | Evidence |
|---|---|---|---|
| 1 | Is an approved specification linked? | | |
| 2 | Is the change within scope? | | |
| 3 | Are acceptance criteria covered by tests? | | |
| 4 | Did validation pass? | | |
| 5 | Are secrets absent? | | |
| 6 | Are dependencies justified? | | |
| 7 | Are protected paths unchanged or approved? | | |
| 8 | Are relevant documents updated? | | |

## Notes on Evidence

- **Validation (Q4):** paste the actual command output (or a summary + link) for `pytest`, `ruff check .`, `mypy src`, `black --check .`, and `pip-audit` (`pip-audit` only if a dependency changed).
- **Secrets (Q5):** confirm no hardcoded credentials were introduced — e.g. "grep for common secret patterns: none found" or reference to a secret-scanning tool's result.
- **Dependencies (Q6):** point to the specification's "Security and Dependencies" section, or write "N/A — no new dependency."
- **Protected paths (Q7):** list any protected path touched and the approval reference, or write "N/A — none touched."
- **Documents (Q8):** list which of `README.md`, docstrings, or `docs/standards.md` were updated, or "N/A — no documentation impact."

## Outcome

- **Result:** Approved for merge | Changes requested | Rejected
- **Reviewer:** `<name>`
- **Date:** `<YYYY-MM-DD>`
