#!/usr/bin/env python3
"""Apply exact Texas AI Docket publication furniture to ImageGen artwork."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

SIZE = 1080
SCRIPT_DIR = Path(__file__).resolve().parent
FONT_DIR = SCRIPT_DIR / "fonts"
FONT_URLS = {
    "Fraunces.ttf": "https://github.com/google/fonts/raw/main/ofl/fraunces/Fraunces%5BSOFT%2CWONK%2Copsz%2Cwght%5D.ttf",
    "JetBrainsMono.ttf": "https://github.com/JetBrains/JetBrainsMono/raw/master/fonts/ttf/JetBrainsMono-Medium.ttf",
}
FALLBACK_SERIF = [
    "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
]
FALLBACK_MONO = [
    "/System/Library/Fonts/Supplemental/Courier New Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_font(filename: str, fallbacks: list[str]) -> str:
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    destination = FONT_DIR / filename
    if destination.is_file() and destination.stat().st_size > 1000:
        return str(destination)
    try:
        request = urllib.request.Request(FONT_URLS[filename], headers={"User-Agent": "TexasDesk/1"})
        with urllib.request.urlopen(request, timeout=25) as response:
            data = response.read()
        if len(data) > 1000:
            destination.write_bytes(data)
            return str(destination)
    except Exception:
        pass
    for candidate in fallbacks:
        if Path(candidate).is_file():
            return candidate
    raise RuntimeError(f"No usable font found for {filename}")


def font_pair() -> tuple[str, str]:
    return (
        ensure_font("Fraunces.ttf", FALLBACK_SERIF),
        ensure_font("JetBrainsMono.ttf", FALLBACK_MONO),
    )


def tracked_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont,
                  tracking: int) -> int:
    return sum(int(draw.textlength(ch, font=font)) + tracking for ch in text) - tracking


def draw_tracked(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str,
                 font: ImageFont.FreeTypeFont, fill: str, tracking: int) -> None:
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += int(draw.textlength(ch, font=font)) + tracking


def star_points(cx: float, cy: float, radius: float) -> list[tuple[float, float]]:
    points = []
    for index in range(10):
        angle = math.radians(-90 + 36 * index)
        length = radius if index % 2 == 0 else radius * 0.43
        points.append((cx + math.cos(angle) * length, cy + math.sin(angle) * length))
    return points


def wrap_headline(draw: ImageDraw.ImageDraw, text: str, font_path: str,
                  max_width: int, max_lines: int = 3) -> tuple[list[str], ImageFont.FreeTypeFont]:
    forced = [part.strip() for part in text.replace("\\n", "\n").splitlines() if part.strip()]
    words = " ".join(forced).split()
    if not words:
        raise ValueError("headline is empty")
    for size in range(96, 51, -2):
        font = ImageFont.truetype(font_path, size)
        lines: list[str] = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if draw.textlength(candidate, font=font) <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        if len(lines) <= max_lines and all(draw.textlength(line, font=font) <= max_width for line in lines):
            return lines, font
    raise ValueError("headline is too long for the cover; rewrite it to 4 to 9 words")


def compose(*, base_path: Path, headline: str, role: str, date: str, place: str,
            coords: str, prompt_file: Path | None, source: str, out_path: Path) -> Path:
    if role not in {"FOUNDER", "OPERATOR", "PUBLIC", "RESEARCH"}:
        raise ValueError("role must be FOUNDER, OPERATOR, PUBLIC, or RESEARCH")
    if source not in {"imagegen", "fallback"}:
        raise ValueError("source must be imagegen or fallback")
    serif_path, mono_path = font_pair()

    base = Image.open(base_path).convert("RGB")
    canvas = ImageOps.fit(base, (SIZE, SIZE), method=Image.Resampling.LANCZOS)
    canvas = ImageEnhance.Contrast(canvas).enhance(1.04)

    # Quiet bands preserve the generated art while guaranteeing exact type remains legible.
    overlay = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    pixels = overlay.load()
    for y in range(SIZE):
        top_alpha = max(0, int(190 * (1 - y / 330))) if y < 330 else 0
        bottom_alpha = max(0, int(225 * ((y - 560) / 520))) if y > 560 else 0
        alpha = max(top_alpha, bottom_alpha)
        for x in range(SIZE):
            pixels[x, y] = (8, 6, 15, alpha)
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(canvas)

    wordmark_font = ImageFont.truetype(serif_path, 42)
    mono_font = ImageFont.truetype(mono_path, 17)
    footer_font = ImageFont.truetype(mono_path, 15)

    draw.polygon(star_points(76, 72, 21), fill="#FFFFFF")
    draw.text((112, 43), "TEXAS AI DOCKET", font=wordmark_font, fill="#F6F1E4")
    kicker = f"TEXAS DESK · {role} · {date}".upper()
    kicker_width = tracked_width(draw, kicker, mono_font, 2)
    draw_tracked(draw, (SIZE - 64 - kicker_width, 104), kicker, mono_font, "#E0956A", 2)
    draw.line((64, 151, SIZE - 64, 151), fill="#E0956A", width=2)

    lines, headline_font = wrap_headline(draw, headline, serif_path, SIZE - 128)
    line_height = int(headline_font.size * 1.02)
    headline_y = 700 - max(0, len(lines) - 2) * 42
    for index, line in enumerate(lines):
        draw.text((64, headline_y + index * line_height), line, font=headline_font, fill="#F6F1E4")

    footer_y = 1001
    draw.line((64, 967, SIZE - 64, 967), fill="#C9B393", width=1)
    location = place.upper().strip()
    if coords.strip():
        location = f"{location} · {coords.strip()}"
    draw_tracked(draw, (64, footer_y), location, footer_font, "#C9B393", 1)
    site = "TEXASAIDOCKET.COM"
    site_width = tracked_width(draw, site, footer_font, 1)
    draw_tracked(draw, (SIZE - 64 - site_width, footer_y), site, footer_font, "#C9B393", 1)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out_path, "PNG", optimize=True)
    prompt_sha = sha256(prompt_file) if prompt_file and prompt_file.is_file() else "unavailable"
    meta = {
        "schema_version": 1,
        "date": date,
        "column": "Texas Desk",
        "kicker": "TEXAS DESK",
        "role": role,
        "headline": headline.replace("\\n", " ").replace("\n", " "),
        "place": place,
        "coordinates": coords,
        "style_family": "story-specific generated editorial art" if source == "imagegen" else "deterministic dusk fallback",
        "palette": ["#08060F", "#0F0C1C", "#F6F1E4", "#C9B393", "#E0956A"],
        "hue_family": "story-derived over Big Bend dusk furniture",
        "composition": "generated full-bleed focal field with fixed top and bottom type bands",
        "motifs": ["story-specific focal metaphor", "single Lone Star"],
        "technique_stack": [source, "deterministic typography overlay"],
        "source": source,
        "seed": "imagegen-managed" if source == "imagegen" else 1701,
        "base_sha256": sha256(base_path),
        "prompt_sha256": prompt_sha,
        "rendered_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "canvas": [SIZE, SIZE],
    }
    Path(str(out_path) + ".meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--headline", required=True)
    parser.add_argument("--role", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--place", required=True)
    parser.add_argument("--coords", default="")
    parser.add_argument("--prompt-file")
    parser.add_argument("--source", choices=("imagegen", "fallback"), default="imagegen")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    result = compose(
        base_path=Path(args.base), headline=args.headline, role=args.role,
        date=args.date, place=args.place, coords=args.coords,
        prompt_file=Path(args.prompt_file) if args.prompt_file else None,
        source=args.source, out_path=Path(args.out),
    )
    print(f"Saved {result}")


if __name__ == "__main__":
    main()
