#!/usr/bin/env python3
"""Technical image and metadata check for a composed Texas Desk cover.

Coded provenance (hashes, anchors, variety, visual review) is enforced by art_gate.validate_art,
which validate_run calls for every profile. This script checks the cover file and its sidecar.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

MAX_BYTES = 5 * 1024 * 1024
REQUIRED_META = [
    "date", "column", "kicker", "role", "headline", "place", "source", "style_family",
    "palette", "composition", "seed", "base_sha256",
]
SOURCES = {"coded", "imagegen"}  # imagegen is legacy and valid only for historical examples


def validate(image_path: Path, date: str, column: str) -> list[str]:
    errors: list[str] = []
    if not image_path.is_file():
        return [f"{image_path} does not exist"]
    try:
        with Image.open(image_path) as opened:
            image_format, image_size = opened.format, opened.size
            pixels = np.asarray(opened.convert("RGB"), dtype=float)
    except Exception as exc:
        return [f"image cannot be opened: {exc}"]
    if image_format != "PNG":
        errors.append(f"format is {image_format}, expected PNG")
    if image_size != (1080, 1080):
        errors.append(f"dimensions are {image_size}, expected 1080 by 1080")
    if image_path.stat().st_size > MAX_BYTES:
        errors.append("file exceeds the 5 MB limit")
    if pixels.std() < 4:
        errors.append(f"pixel standard deviation {pixels.std():.1f} suggests a blank image")

    meta_path = Path(str(image_path) + ".meta.json")
    if not meta_path.is_file():
        return errors + ["metadata sidecar is missing"]
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return errors + [f"metadata sidecar is invalid: {exc}"]
    for key in REQUIRED_META:
        if meta.get(key) in (None, "", []):
            errors.append(f"metadata missing {key}")
    if meta.get("date") != date:
        errors.append(f"metadata date {meta.get('date')!r} does not match {date!r}")
    if meta.get("kicker") != column:
        errors.append(f"metadata kicker {meta.get('kicker')!r} does not match {column!r}")
    if meta.get("source") not in SOURCES:
        errors.append("metadata source must be coded (or legacy imagegen for historical examples)")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--column", required=True)
    args = parser.parse_args()
    errors = validate(Path(args.image), args.date, args.column)
    if errors:
        print("FAIL: artwork")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"PASS: {args.image} passes the technical cover check")
    return 0


if __name__ == "__main__":
    sys.exit(main())
