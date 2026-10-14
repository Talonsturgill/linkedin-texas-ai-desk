#!/usr/bin/env python3
"""Preflight the coded-art renderer: match tested dependencies, then render a smoke image.

A missing or drifted dependency is repairable setup (installed from requirements.txt), not an artwork
provider blocker. The result is coded_art=available only after a real render verifies its size.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS = ROOT / ".agents/skills/texas-desk-artwork/scripts"
REQUIREMENTS = ROOT / "requirements.txt"


def ensure_dependencies() -> list[str]:
    """Repair missing or drifted distributions before importing rendering modules."""
    missing = []
    modules = {"Pillow": "PIL", "numpy": "numpy", "PyYAML": "yaml"}
    pins = {}
    for line in REQUIREMENTS.read_text().splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.fullmatch(r"([A-Za-z0-9_-]+)==([0-9.]+)", line.strip())
        if not match:
            raise ValueError("render dependencies must use exact tested version pins")
        pins[match[1]] = match[2]
    if set(pins) != set(modules):
        raise ValueError("render dependency pins are incomplete")
    for package, module in modules.items():
        try:
            installed = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            installed = None
        if installed != pins[package] or importlib.util.find_spec(module) is None:
            missing.append(package)
    if not missing:
        return []
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", "-r", str(REQUIREMENTS)],
        check=True, timeout=600,
    )
    importlib.invalidate_caches()
    for package in modules:
        if importlib.metadata.version(package) != pins[package]:
            raise RuntimeError("dependency repair did not install the tested version")
    return missing


def smoke(output: Path) -> dict:
    repaired = ensure_dependencies()
    sys.path.insert(0, str(SKILL_SCRIPTS))
    from art_kit import smoke_render  # noqa: E402

    output.parent.mkdir(parents=True, exist_ok=True)
    width, height = smoke_render(output)
    from PIL import Image  # noqa: E402
    from PIL import features  # noqa: E402

    with Image.open(output) as image:
        ok = image.format == "PNG" and image.size == (128, 128) and image.mode == "RGB"
    return {
        "coded_art": "available" if ok and (width, height) == (128, 128) else "unavailable",
        "size": [width, height],
        "dependencies_repaired": repaired,
        "renderer": "pillow+numpy",
        "versions": {name: importlib.metadata.version(name) for name in ("Pillow", "numpy", "PyYAML")},
        "libraries": {name: features.version(name) for name in ("freetype2", "zlib", "raqm")},
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
