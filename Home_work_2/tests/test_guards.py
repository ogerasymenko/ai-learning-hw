from pathlib import Path

from app.guards import Guard, cap, redact


def test_secrets_are_redacted():
    text, hits = redact("key=sk-ant-api03-abcdefghijklmnop")
    assert hits == 1
    assert "[REDACTED:anthropic-key]" in text


def test_output_is_capped():
    text, truncated = cap("x" * 500, 100)
    assert truncated
    assert "showed 100 of 500 chars" in text


def test_allowlist_and_loop_guard(tmp_path: Path):
    guard = Guard(
        allowed_tools={"plan_summary", "resource_changes", "risk_context"},
        max_tool_calls=3,
        max_repeats=2,
        max_tool_chars=4000,
        context_budget_chars=20000,
        log_dir=tmp_path,
    )
    assert not guard.before_tool("Bash", {})[0]
    assert guard.before_tool("plan_summary", {})[0]
    assert guard.before_tool("plan_summary", {})[0]
    assert not guard.before_tool("plan_summary", {})[0]
