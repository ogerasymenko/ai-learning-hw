"""Read-only Terraform plan tools, modeled after the lesson demo's ci-tools.mjs."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_PLAN_PATH = Path(__file__).resolve().parent.parent / "examples" / "plan.json"
MAX_PLAN_BYTES = 5 * 1024 * 1024


class PlanError(ValueError):
    """The supplied plan is unreadable or is not a Terraform plan."""


def parse_plan(text: str) -> dict[str, Any]:
    """Parse and validate `terraform show -json` output."""
    if not text.strip():
        raise PlanError("plan input is empty")
    try:
        plan = json.loads(text)
    except json.JSONDecodeError as exc:
        raise PlanError(f"plan is not valid JSON: {exc}") from exc
    if not isinstance(plan, dict):
        raise PlanError("plan must be a JSON object (terraform show -json output)")
    changes = plan.get("resource_changes", [])
    if not isinstance(changes, list) or not all(isinstance(r, dict) for r in changes):
        raise PlanError("plan.resource_changes must be a list of objects")
    return plan


def load_plan(path: Path = DEFAULT_PLAN_PATH) -> dict[str, Any]:
    try:
        size = path.stat().st_size
        if size > MAX_PLAN_BYTES:
            raise PlanError(f"plan file is {size} bytes; the limit is {MAX_PLAN_BYTES}")
        return parse_plan(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise PlanError(f"cannot read plan file: {exc}") from exc


def read_plan_stream(stream) -> dict[str, Any]:
    data = stream.read(MAX_PLAN_BYTES + 1)
    if len(data) > MAX_PLAN_BYTES:
        raise PlanError(f"plan input exceeds the {MAX_PLAN_BYTES} byte limit")
    return parse_plan(data)


def plan_addresses(plan: dict[str, Any]) -> set[str]:
    return {r.get("address", "unknown") for r in plan.get("resource_changes", [])}


def plan_summary(plan: dict[str, Any]) -> str:
    """What will Terraform change?"""
    counts = {"create": 0, "update": 0, "delete": 0, "replace": 0}
    unchanged = 0
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
        else:
            unchanged += 1  # no-op / read / unknown action lists

    lines = [
        f"Terraform {plan.get('terraform_version', 'unknown')} plan",
        f"create: {counts['create']}",
        f"update: {counts['update']}",
        f"delete: {counts['delete']}",
        f"replace: {counts['replace']}",
        f"no-op/read: {unchanged}",
    ]
    for action in ("create", "update", "delete", "replace"):
        if addresses[action]:
            lines.append(f"{action}: {', '.join(addresses[action])}")
    return "\n".join(lines)


def resource_changes(plan: dict[str, Any], resource: str | None = None) -> str:
    """What exactly changed for a resource?"""
    resources = plan.get("resource_changes", [])
    if resource:
        resources = [r for r in resources if r.get("address") == resource]
        if not resources:
            available = ", ".join(r.get("address", "unknown") for r in plan.get("resource_changes", []))
            raise ValueError(f"No resource named '{resource}'. Available: {available}")

    return json.dumps(resources, indent=2, ensure_ascii=False)


def risk_findings(plan: dict[str, Any]) -> list[str]:
    """Deterministically identify obvious risk signals in the plan."""
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

    return findings


def risk_context(plan: dict[str, Any]) -> str:
    """What deterministic risk signals are present? (text form of risk_findings)"""
    findings = risk_findings(plan)
    return "\n".join(findings) if findings else "No deterministic high-signal risk found."
