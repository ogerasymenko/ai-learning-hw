# Homework 4 — MCP-enabled DevOps agent

## What's in `Home_work_4/`

- **Task 1:** `.mcp.json` connects GitHub (read-only) and Microsoft Learn. Both were used from one natural-language request.
- **Task 2:** `AGENTS.md` has the 5 rules from the PDF plus 5 of my own.
- **Task 3:** the `devops-investigate` skill is in `.claude/skills/`, and `skills/` is a symlink to it.
- **Task 4:** `RESULT.md` has the tool calls, what they returned and how the agent used them.
- **Bonus:** the local server `local_mcp/devops_server.py` has two tools and is registered as `local-devops`. It is documented in `RESULT.md` too.

## Setting up a fresh environment

Requires Python 3.10+ (developed on 3.12). Run from the `Home_work_4/` directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

`requirements.txt` has one package, `mcp`, which the local server (`local_mcp/devops_server.py`) needs. GitHub and Microsoft Learn are remote servers and need no install.

Then:

1. Set the GitHub token in your environment (read access to the repo is enough): `export GITHUB_PAT=<your token>`. `.mcp.json` only references it by name.
2. Start Claude Code with `Home_work_4/` as the project, **from the shell where the venv is active**. `.mcp.json` starts the local server with `python3`, so that command must resolve to the venv's Python.
3. Approve the three project servers (`github`, `microsoft-learn`, `local-devops`) and check them with `/mcp`.
4. Send a goal, for example: "The orders-api service in prod is slow and returns 503 during traffic peaks. Check its current state, see whether it is already tracked in my repo, and use Microsoft's documentation to recommend the next action."
