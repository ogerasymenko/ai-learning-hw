"""Run every eval case k times against the real model and report pass^k.

    python -m evals.run            # all cases, k=3
    python -m evals.run -k 5 --case e_prompt_injection

A case passes only if ALL k runs pass (pass^k). Needs ANTHROPIC_API_KEY and spends real tokens:
cases x k agent runs. Exit code 0 only when every selected case passes pass^k.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from app.agent import run_agent
from app.terraform_tools import load_plan

from .cases import CASES, Case

RESULTS_DIR = Path(__file__).resolve().parent / "results"


def run_case(case: Case, k: int, agent_fn: Callable[[dict], dict] = run_agent) -> dict[str, Any]:
    plan = load_plan(case.plan_path)
    runs = []
    for i in range(k):
        try:
            result = agent_fn(plan)
            failures = case.check(result)
        except Exception as exc:  # a crashed run is a failed run, not a crashed harness
            result, failures = {}, [f"run crashed: {type(exc).__name__}: {exc}"]
        runs.append({"run": i + 1, "passed": not failures, "failures": failures,
                     "needs_human": result.get("needs_human"), "turns": result.get("turns"),
                     "verdict": result.get("verdict")})
    return {"case": case.name, "description": case.description, "k": k,
            "passes": sum(r["passed"] for r in runs), "pass_k": all(r["passed"] for r in runs), "runs": runs}


def run_all(cases: list[Case], k: int, agent_fn: Callable[[dict], dict] = run_agent) -> dict[str, Any]:
    results = [run_case(c, k, agent_fn) for c in cases]
    return {"k": k, "all_passed": all(r["pass_k"] for r in results), "cases": results}


def summarize(report: dict[str, Any]) -> str:
    k = report["k"]
    lines = [f"{'case':26} {'runs ok':8} pass^{k}"]
    for c in report["cases"]:
        lines.append(f"{c['case']:26} {c['passes']}/{k:<6} {'PASS' if c['pass_k'] else 'FAIL'}")
        for r in c["runs"]:
            for f in r["failures"]:
                lines.append(f"    run {r['run']}: {f}")
    lines.append("")
    lines.append("ALL CASES PASS^%d" % k if report["all_passed"] else "NOT ALL CASES PASS^%d" % k)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m evals.run", description=__doc__.split("\n\n")[0])
    parser.add_argument("-k", type=int, default=3, help="runs per case (default 3)")
    parser.add_argument("--case", action="append", help="run only this case (repeatable)")
    args = parser.parse_args(argv)
    if args.k < 1:
        parser.error("-k must be >= 1")

    names = {c.name for c in CASES}
    unknown = set(args.case or []) - names
    if unknown:
        parser.error(f"unknown case(s): {', '.join(sorted(unknown))}; choose from {', '.join(sorted(names))}")
    selected = [c for c in CASES if not args.case or c.name in args.case]

    report = run_all(selected, args.k)
    RESULTS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = RESULTS_DIR / f"eval-{stamp}.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(summarize(report))
    print(f"\nfull report: {out}", file=sys.stderr)
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
