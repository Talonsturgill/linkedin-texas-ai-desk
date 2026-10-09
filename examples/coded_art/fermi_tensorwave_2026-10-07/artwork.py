#!/usr/bin/env python3
"""Coded art for the Fermi and TensorWave closing-extension decision.

Historical visual acceptance example, not current news. Medium: lacquered dusk still life. Two
concrete pillars stand over an unbuilt pad. A brass calendar tab runs between them with two paper
date leaves, SEP 30 and OCT 31, taken from the dossier's September 30th and October 31st claims.
The span between the leaves is dashed: the closing conditions are not yet satisfied. No completed
or powered campus is drawn.
"""

import argparse
import sys
from pathlib import Path

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
]


def _kit() -> None:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / ".agents/skills/texas-desk-artwork/scripts"
        if candidate.is_dir():
            sys.path.insert(0, str(candidate))
            return
    raise RuntimeError("texas-desk-artwork scripts not found")


_kit()
from art_kit import Canvas, rect_points, shade  # noqa: E402

SEREIF = next(p for p in FONT_CANDIDATES if Path(p).is_file())
CAPTION = "#0F0C1C"
CARD = "#EDE6D6"
BRASS = [(0.0, "#5C3D1E"), (0.4, "#E0B878"), (0.6, "#FFF3D0"), (1.0, "#4A2E14")]
LACQUER = [(0.0, "#B4664F"), (0.5, "#8C5A3C"), (1.0, "#2B2447")]


def pillar(c: Canvas, x0: float, x1: float, y0: float, y1: float) -> None:
    mask = c.poly_mask([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    c.shadow(mask, dx=14, dy=10, blur=10, alpha=0.5)
    c.fill(mask, c.sheen(0, LACQUER), 1.0)
    c.bevel(mask, -3, 0, "#E4D8C3", 0.7, blur=1.2)
    cap = c.poly_mask([(x0 - 14, y0), (x1 + 14, y0), (x1 + 14, y0 + 16), (x0 - 14, y0 + 16)])
    c.fill(cap, c.sheen(0, [(0, "#E4D8C3"), (1, "#8C5A3C")]), 1.0)


def card(c: Canvas, cx: float, cy: float, w: float, h: float, label: str, angle: float) -> None:
    mask = c.poly_mask(rect_points(cx, cy, w, h, angle))
    c.shadow(mask, dx=12, dy=16, blur=9, alpha=0.55)
    c.fill(mask, CARD, 1.0)
    c.outline(mask, 2.0, CAPTION, 0.9)
    c.fill(c.poly_mask(rect_points(cx, cy - h / 2 + 10, w - 24, 8, angle)), "#B4664F", 1.0)
    c.fill(c.text_mask(cx, cy + 6, label, SEREIF, 34), CAPTION, 1.0)
    rivet = c.ellipse_mask(cx - w / 2 + 16, cy, 6)
    c.fill(rivet, c.sheen(45, BRASS), 1.0)


def render(out: Path) -> Path:
    c = Canvas(background="#2B2447", seed=1701)
    c.img = c.gradient(90, "#2B2447", "#8C5A3C")
    c.radial_glow(760, 230, 420, "#E0956A", alpha=0.35, power=1.8)

    ground = c.poly_mask([(0, 548), (1080, 530), (1080, 1080), (0, 1080)])
    c.fill(ground, c.gradient(90, "#8C5A3C", "#08060F"), 1.0)

    # Two pads with the unbuilt middle outlined in dashes: nothing is built between them.
    left_pad = c.poly_mask([(150, 520), (360, 520), (360, 548), (150, 548)])
    right_pad = c.poly_mask([(720, 520), (930, 520), (930, 548), (720, 548)])
    c.shadow(left_pad, dx=8, dy=10, blur=6, alpha=0.5)
    c.shadow(right_pad, dx=8, dy=10, blur=6, alpha=0.5)
    c.fill(left_pad, "#E4D8C3", 1.0)
    c.fill(right_pad, "#E4D8C3", 1.0)
    gap = [(380, 520), (700, 520), (700, 548), (380, 548), (380, 520)]
    c.fill(c.line_mask(gap, 3, dash=14, gap=10), "#E0956A", 0.95)

    # Pillars that carry the calendar tab.
    pillar(c, 220, 280, 300, 548)
    pillar(c, 800, 860, 300, 548)

    # Calendar tab: solid brass ends, dashed span across the unresolved gap.
    tab_y = 352
    c.fill(c.poly_mask([(250, tab_y - 16), (820, tab_y - 16), (820, tab_y + 16), (250, tab_y + 16)]),
           c.sheen(0, BRASS), 0.0)
    left_span = c.poly_mask([(250, tab_y - 14), (400, tab_y - 14), (400, tab_y + 14), (250, tab_y + 14)])
    right_span = c.poly_mask([(670, tab_y - 14), (820, tab_y - 14), (820, tab_y + 14), (670, tab_y + 14)])
    c.shadow(left_span, dx=8, dy=12, blur=8, alpha=0.5)
    c.shadow(right_span, dx=8, dy=12, blur=8, alpha=0.5)
    c.fill(left_span, c.sheen(0, BRASS), 1.0)
    c.fill(right_span, c.sheen(0, BRASS), 1.0)
    c.fill(c.line_mask([(400, tab_y), (670, tab_y)], 6, dash=18, gap=12), "#E0B878", 0.95)

    # Two dated leaves, one at each end of the tab, hung from the tab's rivets.
    card(c, 300, 452, 200, 104, "SEP 30", -3)
    card(c, 780, 452, 200, 104, "OCT 31", 3)

    c.grain(0.010)
    c.vignette(0.16)
    return c.finish(out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="art_base.png")
    args = parser.parse_args()
    print(render(Path(args.out)))
