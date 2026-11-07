# Homework 4 — MCP-enabled DevOps agent: Task 4 result

Agent: Claude Code, project `Home_work_4`, brand-new session. Servers (`.mcp.json`): `github` (read-only, toolsets `repos,issues`) and `microsoft-learn`.
Test repo: `ogerasymenko/ai-learning-hw`; tracked item: issue #7 "Scaling rules in Azure Container Apps" (open, no comments; asks whether Container Apps scaling rules support an HTTP scaling rule).

## Chain

```
User goal -> AGENTS.md (MCP Tool Usage) -> skill devops-investigate -> github (issue search) -> microsoft-learn (docs search + fetch) -> recommendation
```

## Prompt (a goal, no tool names, no slash command)

> Investigate this deployment problem: my Azure Container Apps app doesn't scale out when traffic grows. Check whether it is already tracked in my repo ogerasymenko/ai-learning-hw, find relevant technical information, and recommend the next action.

## Tools selected, what they returned

| # | Server / tool | Arguments | Result |
|---|---|---|---|
| 1 | built-in `Skill` | `devops-investigate` | skill instructions loaded by the agent itself |
| 2 | built-in `ToolSearch` | `github` | schemas of the github tools |
| 3 | built-in `ToolSearch` | `microsoft-learn docs` | schemas of the three Learn tools |
| 4 | github / `search_issues` | "Azure Container Apps does not scale out when traffic grows", repo `ogerasymenko/ai-learning-hw` | one match: #7 (open, 0 comments) |
| 5 | github / `list_issues` | repo, `perPage: 30` | only #7 exists, so nothing else could match |
| 6 | microsoft-learn / `microsoft_docs_search` | "Azure Container Apps scaling rules not scaling out HTTP concurrent requests troubleshooting" | excerpts of "Set scaling rules" (HTTP, TCP, custom rules, defaults) and an unrelated Heroku migration page |
| 7 | microsoft-learn / `microsoft_docs_fetch` | `learn.microsoft.com/azure/container-apps/scale-app` | full page: limits, default rule, scale behavior, limitations |
| 8 | github / `issue_read` (`get_comments`) | issue 7 | empty list |

Calls 1–3 are setup; the investigation is calls 4–8. No call failed, no write call was made. Calls 5, 7 and 8 were the agent's own additions; the skill does not prescribe them.

## How the agent used the results

- **Tracked? Partly.** #7 is the only issue; it asks only whether HTTP scaling rules are supported and has no symptom, cause or fix. The agent concluded the user's problem is not really tracked.
- **Docs say:** HTTP rules are supported; replicas are added when concurrent requests exceed `concurrentRequests` (default 10), computed every 15 s; default without a rule is HTTP trigger with min 0 / max 10; scale-out is gradual (1, 4, 8, 16, ...); with several rules any one can trigger scaling.
- **Correlation:** "HTTP scaling rules exist" is confirmed by both sources. The cause of the missing scale-out comes from the docs only (the issue gives none). The agent listed likely causes (`maxReplicas` is 1, threshold too high, misconfigured custom rule, traffic to an older revision, Functions app) and said it cannot confirm them without the app config. Nothing contradicted anything.
- **Next action:** a suggested comment for #7 with a diagnostic checklist (`az containerapp show ... --query properties.template.scale`, check `maxReplicas`, `activeRevisionsMode`, Azure Monitor metrics). The agent posted nothing.
- **Sources and failed calls:** listed per server and tool; no troubleshooting-specific doc page was found, and the real app config was not seen.

## What the run shows

- The skill was loaded automatically (call 1) from a plain goal, then followed in its four steps and output format.
- Tools from both servers were selected from the goal; I named none.
- Behavior matched the `AGENTS.md` MCP rules: read-only (no write calls), facts tied to a source, uncertainty stated instead of invented, the failure/gap report included.
- An earlier run with the same kind of goal found no issue for an unrelated problem ("Provisioning") and correctly answered "not tracked".

## Problems found on the way

- The first session did not use the skill: it was a symlink in `.claude/skills/` and was not discovered. Fix: the real file lives in `.claude/skills/devops-investigate/SKILL.md` (`skills/` is a symlink to it), and `CLAUDE.md` imports `AGENTS.md`.

---

# Bonus — local MCP server + external MCP servers

Local server: `local_mcp/devops_server.py` (stdio, official `mcp` SDK), two read-only tools returning structured data from `local_mcp/data/deployments.json`: `get_environment_status(environment)` and `get_deployment_info(service, environment)`. Registered as `local-devops` in `.mcp.json`. Checked first with a real MCP client over stdio (tools listed, both calls returned structured content, an unknown service returned an error).

## Prompt (goal, no tool names)

> The orders-api service in prod is slow and returns 503 during traffic peaks. Check its current state, see whether it is already tracked in my repo ogerasymenko/ai-learning-hw, and use Microsoft's documentation to recommend the next action.

## Flow

```
Agent -> local-devops (environment status, deployment info) -> github (search_issues) -> microsoft-learn (docs search) -> combined result
```

| Server / tool | What it returned |
|---|---|
| local-devops / `get_environment_status` | prod degraded; only orders-api unhealthy; alerts: p95 4.8 s (threshold 1 s) for 25 min, 6% HTTP 503 at peak |
| local-devops / `get_deployment_info` | Container Apps, revision `orders-api--0000042`, image 1.14.2, replicas 1 / min 1 / max 1, HTTP rule 50 concurrent requests, average load 180, CPU 91% |
| github / `search_issues` (3 queries: "orders-api", "503", "scale replicas latency") | 0 results |
| microsoft-learn / `microsoft_docs_search` | HTTP rule adds replicas only up to `maxReplicas`; concurrency measured every 15 s; replica counts are a target; example with `--max-replicas 10` and concurrency 50 |

No call failed; no write call was made. The agent opened no docs page in full because the excerpts were enough.

## How the agent combined the results

- **Confirmed by local state and docs:** the scale rule exists but has no headroom because `maxReplicas` is 1, which fits slowness and 503s at peak (average load is 3.6x the rule threshold).
- **One source only:** the link between the cap and the 503s is the agent's own inference; the docs do not state it. The agent said it did not check logs, so a regression in image 1.14.2 or a dependency problem is not ruled out.
- **Tracked?** Not tracked (0 search results). Issue #7 was not found by these queries; it is a general question about HTTP scaling rules, not about this service.
- **Next action:** open a new issue (title and body drafted, not created): raise `maxReplicas` (for example to 10, keep `minReplicas` at 1 or higher), then confirm latency and 503s drop and check whether the 18:20Z deploy introduced a regression.

## What the bonus shows

- Local and external servers worked in one run: local facts gave the symptom and cause, GitHub checked tracking, Learn gave the documented behavior.
- The answer follows the skill's output format (local state, tracked, docs, correlation, next action, sources and failed calls). The pasted output does not show an explicit skill call, so I treat skill use as consistent with the format, not proven for this run.
- Claims are separated into confirmed and inferred, the agent drew the line at what the data could prove, and it made no changes.
