# Terraform Plan Explainer

A small Python agent based directly on the Module 2 demo architecture.

The original demo's CI triage agent has three read-only tools, bounded turns/cost/context,
input firewalling, loop guards, audit logging, and explicit untrusted-input rules.
This project keeps those ideas and changes only the domain from CI failures to Terraform plans.

## Structure

- `app/agent.py` — raw Anthropic tool-calling loop, analogous to `raw-loop.mjs` / `triage.mjs`.
- `app/verdict.py` — structured final verdict (`submit_verdict` schema, Pydantic validation, forced human review).
- `app/terraform_tools.py` — three narrow read-only tools, analogous to `ci-tools.mjs`.
- `app/guards.py` — allowlist, call budget, repeat guard, output redaction/cap, audit log.
- `app/main.py` — CLI entry point (file, stdin, or the bundled sample).
- `examples/plan.json` — sample Terraform `show -json`-like input.
- `examples/plan-poisoned.json` — prompt-injection test fixture.
- `tests/` — guard, tool, verdict, CLI, agent-loop and eval-harness tests; no API key required.
- `evals/` — pass^k evaluation harness: the five card cases as fixtures (`evals/fixtures/`), assertions (`evals/cases.py`) and the runner (`evals/run.py`).
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

Pick the plan to explain:

```bash
python -m app.main                      # bundled sample, examples/plan.json
python -m app.main path/to/plan.json    # a file made with `terraform show -json plan.out > plan.json`
terraform show -json plan.out | python -m app.main   # straight from stdin ('-' also works)
python -m app.main plan.json --json     # print only the validated verdict as JSON
```

Exit codes: `0` verdict produced, `1` run stopped (timeout, API error), `2` the plan could not be read
or is not a Terraform plan. Plans larger than 5 MB are rejected.

## Evaluate the agent (pass^3)

```bash
python -m evals.run  # 5 cases x 3 runs against the real model
python -m evals.run -k 5 --case e_prompt_injection
```

Each case runs `k` times (default 3) and passes only if **every** run passes. Assertions use the
structured verdict, not free text: the right resource flagged with the right category and severity,
`needs_human` set correctly, no false alarms on the clean plan, injected text reported in
`suspicious_input`, and no denied (forbidden) tool calls. A crashed or timed-out run counts as a
failure. The full report goes to `evals/results/` (git-ignored); exit code is `0` only if all
cases pass. This calls the API and spends tokens (cases x k runs), so it needs `ANTHROPIC_API_KEY`
and is not part of `pytest`; `tests/test_evals.py` checks the harness itself offline.

## Structured verdict

The model ends the run by calling `submit_verdict` (summary, findings, `needs_human`,
`suspicious_input`). The input is validated with Pydantic: wrong enums, missing fields, or a finding
about a resource that is not in the plan are sent back to the model as errors. If no valid verdict
arrives, the last turn forces the tool, and a run that still fails reports `needs_human: true`.
`needs_human` can only be raised by the model, never lowered below the deterministic `risk_context`
signals or reported suspicious input.

## Safety model

The agent has no shell tool and no Terraform write tool. It can only call:

- `plan_summary`
- `resource_changes`
- `risk_context`
- `submit_verdict` (returns the answer to the caller; changes nothing)

Terraform plan content is untrusted data. The deterministic post-checks and guards are kept
outside the model so the model cannot grant itself write access or bypass the tool limits.
