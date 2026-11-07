---
name: devops-investigate
description: Investigate a deployment or infrastructure problem. Use when the user reports a failing deploy, error or outage and wants to know if it is already tracked, what the docs say, and what to do next.
---

# DevOps investigate

Read-only. Follow the MCP rules in AGENTS.md.

0. **Check the real state (local-devops), when a service or environment is named.** Get its environment status and deployment info (revision, replicas, scale rules, alerts). Use these facts as the symptom in the next steps.
1. **Find the work item (github).** Extract the key symptom (error text, service, resource). Search issues in the user's repo for it, and open the best matches. If nothing matches, say "not tracked".
2. **Get technical facts (microsoft-learn).** Search the official docs for the symptom or the service involved. Open the most relevant page for exact limits, causes or fixes.
3. **Correlate.** Compare the sources (local state, issue, docs): does the issue's cause or fix agree with the docs? Mark each point as confirmed by both, by one source, or contradicted.
4. **Recommend one next action,** and name who does it: comment on issue #N, open a new issue (title and body drafted, not created), or apply a documented fix. Do not make the change yourself.

## Output

- Local state (what `local-devops` reports, if used)
- Tracked? (issue links, or "not tracked")
- Docs say (short, with URLs)
- Correlation (confirmed / one source / contradicted)
- Next action (one)
- Sources and failed calls (server and tool, plus anything that returned nothing or errored)
