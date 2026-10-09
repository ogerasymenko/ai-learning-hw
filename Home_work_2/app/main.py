from __future__ import annotations

import json

from .agent import run_agent


def main() -> int:
    try:
        result = run_agent()
        print("\n──────── Terraform plan verdict ────────")
        print(result["answer"])
        print("\n──────── run stats ────────")
        print(json.dumps({k: v for k, v in result.items() if k != "answer"}, indent=2))
        return 0
    except Exception as exc:
        print(f"stopped: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
