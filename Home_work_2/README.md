# Terraform Plan Explainer

A small Python agent based directly on the Module 2 demo architecture.

The original demo's CI triage agent has three read-only tools, bounded turns/cost/context,
input firewalling, loop guards, audit logging, and explicit untrusted-input rules.
This project keeps those ideas and changes only the domain from CI failures to Terraform plans.

## Structure

- `app/agent.py` — raw Anthropic tool-calling loop, analogous to `raw-loop.mjs` / `triage.mjs`.
- `app/terraform_tools.py` — three narrow read-only tools, analogous to `ci-tools.mjs`.
- `app/guards.py` — allowlist, call budget, repeat guard, output redaction/cap, audit log.
- `app/main.py` — CLI entry point.
- `examples/plan.json` — sample Terraform `show -json`-like input.
- `examples/plan-poisoned.json` — prompt-injection test fixture.
- `tests/` — guard and deterministic-tool tests; no API key required.
- `AGENTS.md` — operational rules for the agent.

## Run tests

```bash
python -m pytest -q
```

## Run the agent

Create and activate a Python virtual environment, then install the project dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Export ANTHROPIC_API_KEY and run agent:

```bash
export ANTHROPIC_API_KEY=...
python -m app.main
```

The first version intentionally reads `examples/plan.json`, just as the lesson demo reads its
local fixture data. A later step can replace that fixture with `terraform show -json` output.

## Safety model

The agent has no shell tool and no Terraform write tool. It can only call:

- `plan_summary`
- `resource_changes`
- `risk_context`

Terraform plan content is untrusted data. The deterministic post-checks and guards are kept
outside the model so the model cannot grant itself write access or bypass the tool limits.
