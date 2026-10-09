#!/usr/bin/env python3
"""Preflight the coded-art renderer: repair missing Python dependencies, then render a smoke image.

A missing Pillow or numpy is repairable setup (installed from requirements.txt), not an artwork
provider blocker. The result is coded_art=available only after a real render verifies its size.
"""

from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS = ROOT / ".agents/skills/texas-desk-artwork/scripts"
REQUIREMENTS = ROOT / "requirements.txt"


def ensure_dependencies() -> list[str]:
    """Import Pillow and numpy; install from requirements.txt if either is missing."""
    missing = []
    for module in ("PIL", "numpy"):
        try:
            importlib.import_module(module)
        except ImportError:
            missing.append(module)
    if not missing:
        return []
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", "-r", str(REQUIREMENTS)],
        check=True, timeout=600,
    )
    importlib.invalidate_caches()
    for module in missing:
        importlib.import_module(module)
    return missing


def smoke(output: Path) -> dict:
    repaired = ensure_dependencies()
    sys.path.insert(0, str(SKILL_SCRIPTS))
    from art_kit import smoke_render  # noqa: E402

    output.parent.mkdir(parents=True, exist_ok=True)
    width, height = smoke_render(output)
    from PIL import Image  # noqa: E402

    with Image.open(output) as image:
        ok = image.format == "PNG" and image.size == (128, 128) and image.mode == "RGB"
    return {
        "coded_art": "available" if ok and (width, height) == (128, 128) else "unavailable",
        "size": [width, height],
        "dependencies_repaired": repaired,
        "renderer": "pillow+numpy",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=".local/art_smoke.png")
    args = parser.parse_args()
    target = Path(args.out).resolve()
    if not target.is_relative_to(ROOT / ".local"):
        parser.error("smoke output must stay under ignored .local/")
    try:
        result = smoke(target)
    except Exception as exc:  # report, never crash the gate
        result = {"coded_art": "unavailable", "error": f"{type(exc).__name__}: {exc}"}
    print(json.dumps(result))
    return 0 if result["coded_art"] == "available" else 2


if __name__ == "__main__":
    raise SystemExit(main())
