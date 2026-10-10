#!/usr/bin/env python3
"""Render a story's artwork.py under the bounded attempt budget, then verify the base image.

Ordinary runs allow runtime.json max_image_attempts (two). An engineering pass may pass a higher
--limit explicitly; the count is still recorded in the usage ledger.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from art_gate import ATTEMPT_LIMIT, record_attempt
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workdir", default="out", help="directory containing artwork.py")
    parser.add_argument("--out", default="art_base.png")
    parser.add_argument("--usage", default=str(ROOT / ".local/usage.json"))
    parser.add_argument("--limit", type=int, default=ATTEMPT_LIMIT)
    args = parser.parse_args()
    workdir = Path(args.workdir).resolve()
    try:
        attempt = record_attempt(Path(args.usage).resolve(), args.limit)
    except RuntimeError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 3
    try:
        result = subprocess.run([sys.executable, "-I", "artwork.py", "--out", args.out],
                                cwd=workdir, capture_output=True, text=True, timeout=240)
    except subprocess.TimeoutExpired:
        print(json.dumps({"ok": False, "attempt": attempt, "limit": args.limit,
                          "error": "artwork.py exceeded 240 seconds"}))
        return 1
    target = workdir / args.out
    ok = result.returncode == 0 and target.is_file()
    size = None
    if ok:
        with Image.open(target) as image:
            size = list(image.size)
            ok = image.format == "PNG" and image.size == (1080, 1080)
    print(json.dumps({"ok": ok, "attempt": attempt, "limit": args.limit, "size": size,
                      "stderr": result.stderr[-400:]}))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
