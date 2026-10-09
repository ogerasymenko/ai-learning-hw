"""Read-only Terraform plan tools, modeled after the lesson demo's ci-tools.mjs."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PLAN_PATH = Path(__file__).resolve().parent.parent / "examples" / "plan.json"


def _load_plan(path: Path = PLAN_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def plan_summary(path: Path = PLAN_PATH) -> str:
    """What will Terraform change?"""
    plan = _load_plan(path)
    counts = {"create": 0, "update": 0, "delete": 0, "replace": 0}
    addresses: dict[str, list[str]] = {k: [] for k in counts}

    for resource in plan.get("resource_changes", []):
        actions = resource.get("change", {}).get("actions", [])
        address = resource.get("address", "unknown")
        if actions == ["create"]:
            counts["create"] += 1
            addresses["create"].append(address)
        elif actions == ["update"]:
            counts["update"] += 1
            addresses["update"].append(address)
        elif actions == ["delete"]:
            counts["delete"] += 1
            addresses["delete"].append(address)
        elif set(actions) == {"delete", "create"}:
            counts["replace"] += 1
            addresses["replace"].append(address)

    lines = [
        f"Terraform {plan.get('terraform_version', 'unknown')} plan",
        f"create: {counts['create']}",
        f"update: {counts['update']}",
        f"delete: {counts['delete']}",
        f"replace: {counts['replace']}",
    ]
    for action in ("create", "update", "delete", "replace"):
        if addresses[action]:
            lines.append(f"{action}: {', '.join(addresses[action])}")
    return "\n".join(lines)


def resource_changes(resource: str | None = None, path: Path = PLAN_PATH) -> str:
    """What exactly changed for a resource?"""
    plan = _load_plan(path)
    resources = plan.get("resource_changes", [])
    if resource:
        resources = [r for r in resources if r.get("address") == resource]
        if not resources:
            available = ", ".join(r.get("address", "unknown") for r in plan.get("resource_changes", []))
            raise ValueError(f"No resource named '{resource}'. Available: {available}")

    return json.dumps(resources, indent=2, ensure_ascii=False)


def risk_context(path: Path = PLAN_PATH) -> str:
    """Deterministically identify obvious risk signals in the plan."""
    plan = _load_plan(path)
    findings: list[str] = []

    for resource in plan.get("resource_changes", []):
        address = resource.get("address", "unknown")
        change = resource.get("change", {})
        actions = change.get("actions", [])
        before = json.dumps(change.get("before"), ensure_ascii=False).lower()
        after = json.dumps(change.get("after"), ensure_ascii=False).lower()

        if "delete" in actions:
            findings.append(f"destructive change: {address} has delete action")
        if set(actions) == {"delete", "create"}:
            findings.append(f"replacement: {address} will be destroyed and recreated")
        if any(word in after for word in ("password", "secret", "token", "api_key")):
            findings.append(f"possible secret exposure: {address} contains a sensitive-looking field")
        if "0777" in after or "0.0.0.0/0" in after:
            findings.append(f"potentially broad access: {address} contains a permissive setting")
        if "password" in before and "password" in after:
            findings.append(f"credential-related change: {address}")

    return "\n".join(findings) if findings else "No deterministic high-signal risk found."
