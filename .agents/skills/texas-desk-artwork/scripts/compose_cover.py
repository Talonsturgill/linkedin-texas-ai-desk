#!/usr/bin/env python3
"""Apply exact Texas AI Docket publication furniture to a coded (or legacy ImageGen) base image.

Compositor contract for art planning:
- The focal object of a coded base must sit inside the unobstructed band y = 180..680.
- Dark gradients are confined to the top strip (0..170) and to the headline/footer zone (700..1080),
  so the art between them is not drowned.
- The headline starts at y >= 658 and the fingerprint band used for variety checks is y = 340..540,
  which carries no overlay at all.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps

SIZE = 1080
FOCAL_BAND = (180, 680)
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
ROLES = {"FOUNDER", "OPERATOR", "PUBLIC", "RESEARCH"}
SOURCES = {"coded", "imagegen"}  # imagegen is legacy: historical examples only


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


def overlay_alpha(y: int, tone: str = "dark") -> int:
    """Top strip darkens the wordmark zone; the headline zone darkens toward the bottom.

    ground_tone "light" is for paper-like art: it darkens more strongly at the top (kicker) and
    starts the headline shade at 660 so cream type never sits on pale ground. The focal band
    180..680 keeps the art readable in both tones.
    """
    if tone == "light":
        if y < 200:
            return int(235 * (1 - y / 200))
        if y > 660:
            return int(235 * min(1.0, (y - 660) / 120))
        return 0
    if y < 170:
        return int(170 * (1 - y / 170))
    if y > 700:
        return int(210 * ((y - 700) / 380))
    return 0


def compose(*, base_path: Path, headline: str, role: str, date: str, place: str,
            coords: str, source: str, out_path: Path, art_direction: Path | None = None,
            renderer: Path | None = None, dossier: Path | None = None,
            prompt_file: Path | None = None) -> Path:
    if role not in ROLES:
        raise ValueError("role must be FOUNDER, OPERATOR, PUBLIC, or RESEARCH")
    if source not in SOURCES:
        raise ValueError("source must be coded or imagegen (imagegen is legacy, historical only)")
    if source == "coded" and (art_direction is None or renderer is None or dossier is None):
        raise ValueError("coded covers require art_direction, renderer, and dossier provenance")
    tone = "dark"
    if source == "coded":
        tone = json.loads(art_direction.read_text(encoding="utf-8")).get("ground_tone", "dark")
    serif_path, mono_path = font_pair()

    base = Image.open(base_path).convert("RGB")
    canvas = ImageOps.fit(base, (SIZE, SIZE), method=Image.Resampling.LANCZOS)
    canvas = ImageEnhance.Contrast(canvas).enhance(1.02)

    overlay = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    for y in range(SIZE):
        alpha = overlay_alpha(y, tone)
        if alpha:
            draw_overlay.line([(0, y), (SIZE, y)], fill=(8, 6, 15, alpha))
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

    meta = {
        "schema_version": 2,
        "date": date,
        "column": "Texas Desk",
        "kicker": "TEXAS DESK",
        "role": role,
        "headline": headline.replace("\\n", " ").replace("\n", " "),
        "place": place,
        "coordinates": coords,
        "source": source,
        "palette": ["#08060F", "#0F0C1C", "#F6F1E4", "#C9B393", "#E0956A"],
        "composition": "coded focal object in 180..680 band with fixed top and bottom type zones",
        "motifs": ["story-specific focal metaphor", "single Lone Star"],
        "technique_stack": ["deterministic typography overlay"],
        "base_sha256": sha256(base_path),
        "rendered_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "canvas": [SIZE, SIZE],
    }
    if source == "coded":
        manifest = json.loads(art_direction.read_text(encoding="utf-8"))
        meta.update({
            "style_family": manifest["style_family"],
            "composition": manifest["composition"],
            "palette_key": manifest["palette_key"],
            "palette": manifest["palette"],
            "material": manifest["material"],
            "silhouette": manifest["silhouette"],
            "light_model": manifest["light_model"],
            "technique_stack": ["pillow+numpy coded art", "deterministic typography overlay"],
            "renderer_sha256": sha256(renderer),
            "dossier_sha256": sha256(dossier),
            "seed": manifest["renderer"]["seed"],
            "ground_tone": tone,
        })
    else:
        meta.update({
            "style_family": "story-specific generated editorial art (legacy ImageGen)",
            "technique_stack": ["imagegen (legacy, historical example)", "deterministic typography overlay"],
            "prompt_sha256": sha256(prompt_file) if prompt_file and prompt_file.is_file() else "unavailable",
            "seed": "imagegen-managed",
        })
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
    parser.add_argument("--source", choices=sorted(SOURCES), default="coded")
    parser.add_argument("--art-direction")
    parser.add_argument("--renderer")
    parser.add_argument("--dossier")
    parser.add_argument("--prompt-file")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    result = compose(
        base_path=Path(args.base), headline=args.headline, role=args.role,
        date=args.date, place=args.place, coords=args.coords, source=args.source,
        out_path=Path(args.out),
        art_direction=Path(args.art_direction) if args.art_direction else None,
        renderer=Path(args.renderer) if args.renderer else None,
        dossier=Path(args.dossier) if args.dossier else None,
        prompt_file=Path(args.prompt_file) if args.prompt_file else None,
    )
    print(f"Saved {result}")


if __name__ == "__main__":
    main()
