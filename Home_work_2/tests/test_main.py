import io
import json

import pytest

from app import main as main_mod

FAKE_RESULT = {"turns": 1, "verdict": {}, "needs_human": True, "review_reasons": [], "answer": "ANSWER"}


@pytest.fixture
def captured(monkeypatch):
    seen = {}

    def fake_run(plan):
        seen["plan"] = plan
        return FAKE_RESULT

    monkeypatch.setattr(main_mod, "run_agent", fake_run)
    return seen


def test_file_argument(tmp_path, captured, capsys):
    f = tmp_path / "p.json"
    f.write_text(json.dumps({"resource_changes": []}))
    assert main_mod.main([str(f)]) == 0
    assert captured["plan"] == {"resource_changes": []}
    assert "ANSWER" in capsys.readouterr().out


def test_stdin_dash(monkeypatch, captured):
    monkeypatch.setattr("sys.stdin", io.StringIO('{"resource_changes": []}'))
    assert main_mod.main(["-"]) == 0
    assert captured["plan"] == {"resource_changes": []}


def test_piped_stdin_without_argument(monkeypatch, captured):
    monkeypatch.setattr("sys.stdin", io.StringIO('{"resource_changes": []}'))
    assert main_mod.main([]) == 0
    assert captured["plan"] == {"resource_changes": []}


def test_tty_falls_back_to_sample(monkeypatch, captured):
    class Tty(io.StringIO):
        def isatty(self):
            return True

    monkeypatch.setattr("sys.stdin", Tty())
    assert main_mod.main([]) == 0
    assert "aws_security_group.web" in json.dumps(captured["plan"])


def test_invalid_plan_exits_2(monkeypatch, captured, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO("garbage"))
    assert main_mod.main(["-"]) == 2
    assert "invalid plan" in capsys.readouterr().err
    assert "plan" not in captured


def test_json_flag_prints_only_json(tmp_path, captured, capsys):
    f = tmp_path / "p.json"
    f.write_text('{"resource_changes": []}')
    assert main_mod.main([str(f), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["needs_human"] is True
