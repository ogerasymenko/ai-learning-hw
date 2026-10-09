from app.terraform_tools import plan_summary, resource_changes, risk_context


def test_plan_summary_is_deterministic():
    summary = plan_summary()
    assert "create: 1" in summary
    assert "update: 2" in summary
    assert "delete: 1" in summary
    assert "replace: 1" in summary


def test_resource_changes_contains_resource():
    result = resource_changes("aws_security_group.web")
    assert "0.0.0.0/0" in result


def test_risk_context_detects_destructive_and_broad_access():
    result = risk_context()
    assert "destructive change" in result
    assert "potentially broad access" in result
    assert "replacement" in result
