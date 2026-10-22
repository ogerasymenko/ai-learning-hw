from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .agent import run_agent
from .terraform_tools import DEFAULT_PLAN_PATH, PlanError, load_plan, read_plan_stream


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m app.main",
        description="Explain a Terraform plan (read-only). Never applies anything.",
    )
    parser.add_argument(
        "plan", nargs="?",
        help="path to `terraform show -json` output, or '-' for stdin "
             f"(default: piped stdin if present, else {DEFAULT_PLAN_PATH.name} from examples/)",
    )
    parser.add_argument("--json", action="store_true", help="print the validated verdict as JSON only")
    return parser.parse_args(argv)


def read_plan(source: str | None) -> dict:
    if source == "-":
        return read_plan_stream(sys.stdin)
    if source is not None:
        return load_plan(Path(source))
    if not sys.stdin.isatty():
        return read_plan_stream(sys.stdin)
    print(f"no plan given; using the sample {DEFAULT_PLAN_PATH}", file=sys.stderr)
    return load_plan(DEFAULT_PLAN_PATH)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        plan = read_plan(args.plan)
    except PlanError as exc:
        print(f"invalid plan: {exc}", file=sys.stderr)
        return 2

    try:
        result = run_agent(plan)
    except Exception as exc:
        print(f"stopped: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps({k: v for k, v in result.items() if k != "answer"}, indent=2))
    else:
        print("\n──────── Terraform plan verdict ────────")
        print(result["answer"])
        print("\n──────── run stats ────────")
        print(json.dumps({k: v for k, v in result.items() if k not in ("answer", "verdict")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
