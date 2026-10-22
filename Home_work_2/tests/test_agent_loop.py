from types import SimpleNamespace as NS

import pytest

from app import agent
from app.terraform_tools import DEFAULT_PLAN_PATH, load_plan

PLAN = load_plan(DEFAULT_PLAN_PATH)
GOOD = {
    "summary": "s", "needs_human": False, "suspicious_input": [],
    "findings": [{"resource": "aws_security_group.web", "severity": "high", "category": "security",
                  "kind": "fact", "evidence": "0.0.0.0/0"}],
}


def tool(name, input_, id_="t1"):
    return NS(type="tool_use", name=name, input=input_, id=id_)


def reply(*blocks):
    return NS(content=list(blocks), stop_reason="tool_use" if any(b.type == "tool_use" for b in blocks) else "end_turn")


class FakeClient:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []
        self.messages = self

    def create(self, **kw):
        self.calls.append({**kw, "messages": list(kw["messages"])})
        return self.replies.pop(0)


@pytest.fixture
def run(monkeypatch, tmp_path):
    def _run(replies):
        client = FakeClient(replies)
        monkeypatch.setattr(agent, "Anthropic", lambda **kw: client)
        monkeypatch.setattr(agent, "LOG_DIR", tmp_path)
        return agent.run_agent(PLAN), client
    return _run


def test_happy_path_forces_review_from_risk_signals(run):
    result, client = run([
        reply(tool("plan_summary", {})),
        reply(tool("submit_verdict", GOOD)),
    ])
    assert result["verdict"]["findings"][0]["resource"] == "aws_security_group.web"
    assert result["needs_human"] is True  # model said False, deterministic signals override
    assert result["turns"] == 2
    assert client.calls[0]["tool_choice"] == {"type": "auto"}


def test_invalid_verdict_gets_error_and_can_retry(run):
    bad = {**GOOD, "findings": [{**GOOD["findings"][0], "resource": "ghost"}]}
    result, client = run([
        reply(tool("submit_verdict", bad)),
        reply(tool("submit_verdict", GOOD)),
    ])
    assert result["verdict"] is not None
    last_user = client.calls[1]["messages"][-1]["content"][0]
    assert last_user["is_error"] and "not in the plan" in last_user["content"]


def test_free_text_is_nudged_not_accepted(run):
    result, client = run([
        reply(NS(type="text", text="all good")),
        reply(tool("submit_verdict", GOOD)),
    ])
    assert result["verdict"] is not None
    assert "submit_verdict" in client.calls[1]["messages"][-1]["content"]


def test_no_verdict_fails_safe_and_forces_tool_on_last_turn(run):
    replies = [reply(NS(type="text", text="hmm")) for _ in range(agent.LIMITS["max_turns"])]
    result, client = run(replies)
    assert result["verdict"] is None and result["needs_human"] is True
    assert client.calls[-1]["tool_choice"] == {"type": "tool", "name": "submit_verdict"}


def test_unknown_tool_is_denied(run):
    result, client = run([
        reply(tool("Bash", {"command": "terraform apply"})),
        reply(tool("submit_verdict", GOOD)),
    ])
    denied = client.calls[1]["messages"][-1]["content"][0]
    assert denied["is_error"]
    assert result["denied"]
