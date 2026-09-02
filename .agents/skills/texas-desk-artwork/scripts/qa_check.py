#!/usr/bin/env python3
"""Technical gate for a composed Texas Desk cover."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

REQUIRED_META = [
    "date", "column", "kicker", "role", "headline", "place", "style_family",
    "palette", "composition", "motifs", "source", "seed", "base_sha256",
    "prompt_sha256",
]


def validate(image_path: Path, date: str, column: str) -> list[str]:
    errors: list[str] = []
    if not image_path.is_file():
        return [f"{image_path} does not exist"]
    try:
        with Image.open(image_path) as opened:
            image_format = opened.format
            image_size = opened.size
            pixels = np.asarray(opened.convert("RGB"), dtype=float)
            thumbnail = np.asarray(opened.convert("RGB").resize((128, 128)))
    except Exception as exc:
        return [f"image cannot be opened: {exc}"]
    if image_format != "PNG":
        errors.append(f"format is {image_format}, expected PNG")
    if image_size != (1080, 1080):
        errors.append(f"dimensions are {image_size}, expected 1080 by 1080")
    size_kb = image_path.stat().st_size / 1024
    if not 60 <= size_kb <= 6000:
        errors.append(f"file size {size_kb:.0f} KB is outside 60 to 6000 KB")
    if pixels.std() < 15:
        errors.append(f"pixel standard deviation {pixels.std():.1f} suggests a blank image")
    if len(np.unique(thumbnail.reshape(-1, 3), axis=0)) < 60:
        errors.append("thumbnail has too few distinct colors")

    meta_path = Path(str(image_path) + ".meta.json")
    if not meta_path.is_file():
        errors.append("metadata sidecar is missing")
        return errors
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"metadata sidecar is invalid: {exc}")
        return errors
    for key in REQUIRED_META:
        if meta.get(key) in (None, "", []):
            errors.append(f"metadata missing {key}")
    if meta.get("date") != date:
        errors.append(f"metadata date {meta.get('date')!r} does not match {date!r}")
    if meta.get("kicker") != column:
        errors.append(f"metadata kicker {meta.get('kicker')!r} does not match {column!r}")
    if meta.get("source") not in {"imagegen", "fallback"}:
        errors.append("metadata source must be imagegen or fallback")
    if meta.get("source") == "imagegen" and meta.get("prompt_sha256") == "unavailable":
        errors.append("ImageGen cover must retain its prompt hash")
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
    print(f"PASS: {args.image} is a complete 1080 by 1080 Texas Desk cover")
    return 0


if __name__ == "__main__":
    sys.exit(main())
