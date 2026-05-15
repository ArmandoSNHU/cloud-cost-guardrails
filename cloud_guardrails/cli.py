from __future__ import annotations

import argparse
import json
from pathlib import Path

from .policies import evaluate_inventory


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate cloud inventory guardrails.")
    parser.add_argument("inventory", type=Path, help="Path to JSON inventory array.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args()

    resources = json.loads(args.inventory.read_text(encoding="utf-8"))
    findings = evaluate_inventory(resources)
    indent = 2 if args.pretty else None
    print(json.dumps({"finding_count": len(findings), "findings": findings}, indent=indent))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

