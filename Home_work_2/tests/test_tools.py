import pytest

from app.terraform_tools import (
    DEFAULT_PLAN_PATH, PlanError, load_plan, parse_plan, plan_summary,
    read_plan_stream, resource_changes, risk_context,
)

PLAN = load_plan(DEFAULT_PLAN_PATH)


def test_plan_summary_is_deterministic():
    summary = plan_summary(PLAN)
    assert "create: 1" in summary
    assert "update: 2" in summary
    assert "delete: 1" in summary
    assert "replace: 1" in summary


def test_plan_summary_counts_noop_separately():
    plan = {"resource_changes": [
        {"address": "a", "change": {"actions": ["no-op"]}},
        {"address": "b", "change": {"actions": ["read"]}},
        {"address": "c", "change": {"actions": ["create", "delete"]}},
    ]}
    summary = plan_summary(plan)
    assert "no-op/read: 2" in summary
    assert "replace: 1" in summary


def test_resource_changes_contains_resource():
    result = resource_changes(PLAN, "aws_security_group.web")
    assert "0.0.0.0/0" in result


def test_resource_changes_unknown_resource_lists_available():
    with pytest.raises(ValueError, match="aws_security_group.web"):
        resource_changes(PLAN, "nope")


def test_risk_context_detects_destructive_and_broad_access():
    result = risk_context(PLAN)
    assert "destructive change" in result
    assert "potentially broad access" in result
    assert "replacement" in result


def test_empty_plan_is_valid_and_clean():
    plan = parse_plan('{"resource_changes": []}')
    assert "create: 0" in plan_summary(plan)
    assert risk_context(plan) == "No deterministic high-signal risk found."


@pytest.mark.parametrize("text", ["", "   ", "not json", "[1, 2]", '{"resource_changes": {}}', '{"resource_changes": [1]}'])
def test_bad_plans_are_rejected(text):
    with pytest.raises(PlanError):
        parse_plan(text)


def test_load_plan_from_file_and_missing_file(tmp_path):
    f = tmp_path / "p.json"
    f.write_text('{"resource_changes": []}')
    assert load_plan(f) == {"resource_changes": []}
    with pytest.raises(PlanError):
        load_plan(tmp_path / "missing.json")


def test_stream_size_limit(monkeypatch):
    import io
    import app.terraform_tools as tt
    monkeypatch.setattr(tt, "MAX_PLAN_BYTES", 10)
    with pytest.raises(PlanError, match="limit"):
        read_plan_stream(io.StringIO("x" * 50))


def test_poisoned_fixture_loads_as_data():
    plan = load_plan(DEFAULT_PLAN_PATH.with_name("plan-poisoned.json"))
    assert "IGNORE ALL PREVIOUS INSTRUCTIONS" in resource_changes(plan, "aws_security_group.web")
