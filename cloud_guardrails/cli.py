from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .policies import evaluate_inventory


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate cloud inventory guardrails.")
    parser.add_argument("inventory", type=Path, help="Path to JSON inventory array.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args()

    try:
        resources = json.loads(args.inventory.read_text(encoding="utf-8"))
        if not isinstance(resources, list):
            raise ValueError("Expected an array")
        findings = evaluate_inventory(resources)
    except (OSError, UnicodeError, ValueError):
        print(json.dumps({"error": "Invalid inventory: expected resources matching the inventory contract."}), file=sys.stderr)
        return 2
    indent = 2 if args.pretty else None
    print(json.dumps({"finding_count": len(findings), "findings": findings}, indent=indent, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

