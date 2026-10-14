#!/usr/bin/env python3
"""Gate capabilities before spending tokens on research; never read account data."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def assess(capabilities: dict, runtime: dict) -> dict:
    missing = [name for name in runtime["required_capabilities"]
               if capabilities.get(name) != "available"]
    return {
        "ok": not missing,
        "state": "ready" if not missing else "needs-attention",
        "capabilities": {name: capabilities.get(name, "unknown")
                         for name in runtime["required_capabilities"]},
        "missing": missing,
        "configured_model": runtime["model_display_name"],
        "configured_effort": runtime["effort"],
        "environment_effort": os.environ.get("CLAUDE_CODE_EFFORT_LEVEL", "unavailable"),
        "active_model_and_effort": "verify in session; configuration is not runtime proof",
        "measured_token_usage": None,
        "measured_cost_usd": None,
    }


def main() -> int:
    runtime = json.loads((ROOT / "config/runtime.json").read_text())
    parser = argparse.ArgumentParser(description=__doc__)
    for name in runtime["required_capabilities"]:
        parser.add_argument("--" + name.replace("_", "-"),
                            choices=["available", "unavailable", "unknown"], default="unknown")
    parser.add_argument("--out", default=".local/runtime.json")
    args = parser.parse_args()
    target = Path(args.out).resolve()
    if not target.is_relative_to(ROOT / ".local"):
        parser.error("runtime receipts must stay under ignored .local/")
    result = assess(vars(args), runtime)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"state": result["state"], "missing": result["missing"]}))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
