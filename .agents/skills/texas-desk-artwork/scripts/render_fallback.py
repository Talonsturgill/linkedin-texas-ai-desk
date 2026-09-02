#!/usr/bin/env python3
"""Create the deterministic fallback background and compose a Texas Desk cover."""

from __future__ import annotations

import argparse
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from compose_cover import compose

SIZE = 1080


def hex_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))


def background(seed: int = 1701) -> Image.Image:
    rng = np.random.default_rng(seed)
    top = np.array(hex_rgb("#08060F"), dtype=float)
    bottom = np.array(hex_rgb("#191530"), dtype=float)
    array = np.zeros((SIZE, SIZE, 3), dtype=float)
    for y in range(SIZE):
        t = (y / (SIZE - 1)) ** 1.25
        array[y, :, :] = top * (1 - t) + bottom * t

    # Warm dusk veil and paper grain create a Texas-specific fallback, not an aurora template.
    yy, xx = np.mgrid[0:SIZE, 0:SIZE]
    glow = np.exp(-(((xx - 790) / 430) ** 2 + ((yy - 660) / 260) ** 2))
    ember = np.array(hex_rgb("#B4664F"), dtype=float)
    array = array * (1 - glow[..., None] * 0.34) + ember * glow[..., None] * 0.34
    grain = rng.normal(0, 3.8, size=(SIZE, SIZE, 1))
    array = np.clip(array + grain, 0, 255).astype(np.uint8)
    image = Image.fromarray(array, "RGB")

    draw = ImageDraw.Draw(image, "RGBA")
    random.seed(seed)
    horizon = 680
    for layer_index, color in enumerate(("#2B2447", "#4B3651", "#6E4B4D", "#8C5A3C")):
        points = [(0, SIZE)]
        baseline = horizon + layer_index * 60
        for x in range(0, SIZE + 1, 36):
            y = baseline + math.sin(x / (120 + layer_index * 17)) * (28 + layer_index * 8)
            y += random.uniform(-12, 12)
            points.append((x, y))
        points.extend([(SIZE, SIZE), (0, SIZE)])
        draw.polygon(points, fill=(*hex_rgb(color), 235))
    for x in range(70, SIZE, 92):
        draw.line((x, 280, x + 130, 930), fill=(228, 216, 195, 23), width=2)
    image = image.filter(ImageFilter.GaussianBlur(0.35))
    return image


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--headline", required=True)
    parser.add_argument("--role", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--place", required=True)
    parser.add_argument("--coords", default="")
    parser.add_argument("--prompt-file")
    parser.add_argument("--out", required=True)
    parser.add_argument("--base-out")
    args = parser.parse_args()
    out_path = Path(args.out)
    base_path = Path(args.base_out) if args.base_out else out_path.with_name("art_base.png")
    base_path.parent.mkdir(parents=True, exist_ok=True)
    background().save(base_path, "PNG", optimize=True)
    compose(
        base_path=base_path, headline=args.headline, role=args.role,
        date=args.date, place=args.place, coords=args.coords,
        prompt_file=Path(args.prompt_file) if args.prompt_file else None,
        source="fallback", out_path=out_path,
    )
    print(f"Saved fallback cover {out_path}")


if __name__ == "__main__":
    main()
