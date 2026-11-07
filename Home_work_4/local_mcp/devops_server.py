#!/usr/bin/env python3
"""Local MCP server (stdio) with two read-only DevOps tools over mock data.

  get_environment_status(environment)            health, region, per-service status, open alerts
  get_deployment_info(service, environment)      revision, image, replicas, scale rules, metrics

The data is a made-up snapshot in data/deployments.json, so the demo is repeatable.
Run by an MCP client (see ../.mcp.json); stdout carries the protocol, so never print() here.
"""
import json
from typing import Any
from pathlib import Path

try:  # mcp 2.x renamed FastMCP to MCPServer
    from mcp.server.mcpserver import MCPServer as Server
except ImportError:
    from mcp.server.fastmcp import FastMCP as Server

DATA = json.loads((Path(__file__).parent / "data" / "deployments.json").read_text(encoding="utf-8"))

mcp = Server("local-devops")


def _pick(kind: str, value: str, options) -> str:
    key = str(value).strip().lower()
    if key not in options:
        raise ValueError(f"Unknown {kind} {value!r}. Known: {', '.join(sorted(options))}")
    return key


@mcp.tool()
def get_environment_status(environment: str) -> dict[str, Any]:
    """Health of one environment (dev, staging or prod): overall status, region, status of each
    service and open alerts. Start here to see what is unhealthy."""
    env = _pick("environment", environment, DATA["environments"])
    return {"environment": env, **DATA["environments"][env]}


@mcp.tool()
def get_deployment_info(service: str, environment: str = "prod") -> dict[str, Any]:
    """Current deployment of one service in one environment: platform, revision, image, who deployed
    and when, replicas (current/min/max), scale rules, traffic split and live metrics."""
    svc = _pick("service", service, DATA["deployments"])
    env = _pick(f"environment for {svc}", environment, DATA["deployments"][svc])
    return {"service": svc, "environment": env, **DATA["deployments"][svc][env]}


if __name__ == "__main__":
    mcp.run()  # stdio transport
