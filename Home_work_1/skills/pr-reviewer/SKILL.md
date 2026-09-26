# Skill: pr-reviewer

## Purpose and When to Use It

Reviews a proposed change against `review/change-template.md` before it is submitted or merged. Use this skill whenever a change is ready for review, or whenever explicitly asked to review a change or PR.

## Required Inputs

- The diff or list of changed files.
- The linked specification path (and its `Status`).
- The linked plan (`Affected Files / Modules` table), if one exists.
- Validation command output: `pytest`, `ruff check .`, `mypy src`, `black --check .`, and `pip-audit` (if dependencies changed).
- `AGENTS.md` Section 6 (protected paths).

## Step-by-Step Instructions

1. Confirm a specification is linked and its `Status` is `Approved`. If not, this is an automatic **No** on Question 1.
2. Compare the changed files against the specification's Scope and the plan's Affected Files table. Anything outside both is out of scope.
3. For each Acceptance Criterion in the specification, confirm a corresponding test exists in the diff.
4. Check the supplied validation output: all of `pytest`, `ruff check .`, `mypy src`, `black --check .` must show success; `pip-audit` only if a dependency changed.
5. Scan the diff for hardcoded secrets, tokens, or credentials.
6. If a new dependency was added, confirm it is named and justified in the specification's Security and Dependencies section.
7. Compare changed files against the protected-paths list in `AGENTS.md`, Section 6. Any protected path touched must have a recorded approval.
8. Confirm documentation (docstrings, `README.md`, `docs/standards.md`) was updated where the change affects them.
9. Fill in every row of `review/change-template.md` with **Yes**, **No**, or **N/A**, plus evidence for each.
10. Set **Outcome**: `Approved for merge` only if every row is Yes or N/A; otherwise `Changes requested` (or `Rejected` if the change is fundamentally out of scope or unsafe).

## Stop Conditions

- If Question 1 (approved spec linked) is **No**, still complete the rest of the checklist, but the Outcome cannot be `Approved for merge`.
- If a secret is found (Question 5 = No) or a protected path is touched without approval (Question 7 = No), flag this as a blocking issue in the Outcome regardless of other answers.
- Never change the Outcome to `Approved for merge` to avoid blocking someone — a No answer always blocks approval.

## Output Format

A filled-in copy of `review/change-template.md`: the 8-row table with Answer and Evidence columns completed, plus the Outcome section (Result, Reviewer, Date).

## Yes/No Quality Checks

- Are all 8 rows answered with Yes, No, or N/A (none left blank)? Yes/No
- Does every non-N/A answer include evidence (a link, command output, or file reference)? Yes/No
- Is the Outcome consistent with the answers (no `Approved for merge` alongside any blocking No)? Yes/No
- Was `review/change-template.md`'s exact question set used, unchanged? Yes/No

## Example

**Input:** Diff adding `src/health.py` and `tests/test_health.py`, linked to `specs/sample-health-endpoint.md` (`Status: Approved`), with passing `pytest`/`ruff`/`mypy`/`black` output and no new dependency.

**Output (excerpt):**
```markdown
| # | Question | Answer | Evidence |
|---|---|---|---|
| 1 | Is an approved specification linked? | Yes | specs/sample-health-endpoint.md, Status: Approved |
| 4 | Did validation pass? | Yes | pytest: 2 passed; ruff/mypy/black: no issues |
| 5 | Are secrets absent? | Yes | No credential patterns found in diff |

Result: Approved for merge
```
