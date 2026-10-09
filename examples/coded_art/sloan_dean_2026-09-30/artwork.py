#!/usr/bin/env python3
"""Coded art for the AI Hospitality Group operating-model decision.

Historical visual acceptance example, not current news. Medium: lit brass and enamel still life on
an ink-teal ground. A large hotel key (bow, shaft, teeth) and a reception bell are the foreground
objects. Index cards on a brass wire lead to the bell, and the cutaway disc behind the key is
divided into staffing, scheduling and guest service sectors: the operating work the key stands
for. It is a conceptual hotel, not a located Texas property; the dossier names no Texas pilot.
"""

import argparse
import sys
from pathlib import Path


def _kit() -> None:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / ".agents/skills/texas-desk-artwork/scripts"
        if candidate.is_dir():
            sys.path.insert(0, str(candidate))
            return
    raise RuntimeError("texas-desk-artwork scripts not found")


_kit()
import math  # noqa: E402

import numpy as np  # noqa: E402
from art_kit import Canvas, arc_points, rect_points  # noqa: E402

INK = "#0F0C1C"
TEAL = "#1F5C5A"
TEAL_HI = "#3E8A84"
COPPER = "#B4664F"
BRASS = [(0.0, "#3A2510"), (0.3, "#B8864A"), (0.55, "#FFF3D0"), (0.75, "#C9A063"), (1.0, "#3A2510")]
PAPER = "#EDE6D6"


def brass(c: Canvas, mask: np.ndarray, angle: float = 40) -> None:
    c.fill(mask, c.sheen(angle, BRASS))


def render(out: Path) -> Path:
    c = Canvas(background=INK, seed=2026)
    c.radial_glow(600, 420, 470, TEAL, alpha=0.55, power=1.6)
    c.radial_glow(620, 420, 260, COPPER, alpha=0.18, power=2.0)

    # Cutaway disc: three sectors, each a different teal value, ringed in brass.
    cx, cy, r = 610, 430, 215
    disc_shadow = c.ellipse_mask(cx + 26, cy + 30, r, r)
    c.fill(c.blur(disc_shadow, 18), "#000000", 0.55)
    sectors = [(-90, 30, TEAL), (30, 150, "#2A6F6B"), (150, 270, "#174744")]
    for a0, a1, tone in sectors:
        wedge = c.poly_mask([(cx, cy)] + arc_points(cx, cy, r, r, a0, a1))
        c.fill(wedge, c.sheen(60, [(0, tone), (0.6, TEAL_HI), (1, INK)]), 1.0)
    rim = c.ring_mask(cx, cy, r + 12, r + 12, r, r)
    brass(c, rim, 20)
    for angle in (-90, 30, 150):
        spoke = [(cx, cy), (cx + math.cos(math.radians(angle)) * r, cy + math.sin(math.radians(angle)) * r)]
        c.fill(c.line_mask(spoke, 7), "#C9A063", 0.95)

    # Scheduling sector: a brass clock face with hands.
    kx, ky = 668, 318
    clock = c.ellipse_mask(kx, ky, 46)
    c.shadow(clock, dx=6, dy=8, blur=5, alpha=0.5)
    brass(c, clock, 35)
    c.fill(c.ellipse_mask(kx, ky, 36), "#EDE6D6", 0.92)
    c.fill(c.line_mask([(kx, ky), (kx, ky - 26)], 4), INK, 1.0)
    c.fill(c.line_mask([(kx, ky), (kx + 18, ky + 8)], 4), INK, 1.0)

    # Staffing sector: three standing figures, simple shapes with no faces.
    for fx, fy, scale in [(560, 520, 1.0), (606, 530, 1.1), (652, 520, 1.0)]:
        head = c.ellipse_mask(fx, fy - 40 * scale, 11 * scale)
        body = c.poly_mask([(fx - 17 * scale, fy - 26 * scale), (fx + 17 * scale, fy - 26 * scale),
                            (fx + 22 * scale, fy + 22 * scale), (fx - 22 * scale, fy + 22 * scale)])
        c.fill(head, PAPER, 0.92)
        c.fill(body, PAPER, 0.92)

    # Guest service sector: a board of hooks, each with a brass key tag.
    c.fill(c.line_mask([(320, 360), (420, 300)], 6), "#3A2510", 0.9)
    for hx, hy in [(340, 352), (370, 336), (400, 320)]:
        c.fill(c.ellipse_mask(hx, hy, 9), "#C9A063", 0.95)

    # The key: bow (ring), shaft, and three teeth near the tip.
    bow = c.ring_mask(214, 296, 78, 78, 42, 42)
    key_shadow_source = bow
    c.shadow(key_shadow_source, dx=18, dy=24, blur=12, alpha=0.55)
    brass(c, bow, 45)
    c.bevel(bow, -3, -3, "#FFF3D0", 0.8, blur=1.5)
    start, end = (262, 346), (500, 560)
    length = math.hypot(end[0] - start[0], end[1] - start[1])
    angle = math.degrees(math.atan2(end[1] - start[1], end[0] - start[0]))
    mid = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
    shaft = c.poly_mask(rect_points(mid[0], mid[1], length, 26, angle))
    c.shadow(shaft, dx=18, dy=24, blur=12, alpha=0.55)
    brass(c, shaft, 45)
    c.bevel(shaft, -2, -3, "#FFF3D0", 0.75, blur=1.2)
    for t in (0.74, 0.84, 0.94):
        px = start[0] + (end[0] - start[0]) * t
        py = start[1] + (end[1] - start[1]) * t
        tooth = c.poly_mask(rect_points(px, py, 22, 16, angle + 90))
        c.shadow(tooth, dx=10, dy=14, blur=6, alpha=0.45)
        brass(c, tooth, 45)

    # Reception bell: a domed brass bell on a flared base, lit from the upper left.
    bx, by = 862, 500
    base_shadow = c.ellipse_mask(bx + 30, by + 98, 150, 30)
    c.fill(c.blur(base_shadow, 12), "#000000", 0.55)
    dome = c.poly_mask(arc_points(bx, by, 96, 80, 180, 360) + [(bx + 96, by + 4), (bx - 96, by + 4)])
    c.shadow(dome, dx=10, dy=12, blur=8, alpha=0.4)
    brass(c, dome, 0)
    c.bevel(dome, -6, -4, "#FFF3D0", 0.9, blur=2.0)
    flare = c.poly_mask([(bx - 96, by + 4), (bx + 96, by + 4), (bx + 128, by + 74), (bx - 128, by + 74)])
    brass(c, flare, 5)
    base = c.ellipse_mask(bx, by + 74, 132, 28)
    c.shadow(base, dx=8, dy=10, blur=6, alpha=0.45)
    brass(c, base, 60)
    knob = c.ellipse_mask(bx, by - 84, 16)
    brass(c, knob, 30)

    # Workflow cards on a brass wire running to the bell's knob.
    wire = [(790, 300), (836, 360), (bx, by - 84)]
    c.fill(c.line_mask(wire, 4), "#C9A063", 0.95)
    for i, (ccx, ccy, angle_deg, tab) in enumerate([(730, 232, -7, TEAL_HI), (800, 250, 3, COPPER), (862, 220, 9, "#C9A063")]):
        card = c.poly_mask(rect_points(ccx, ccy, 128, 88, angle_deg))
        c.shadow(card, dx=8, dy=12, blur=7, alpha=0.5)
        c.fill(card, PAPER, 0.96)
        c.fill(c.poly_mask(rect_points(ccx - 26, ccy - 40, 46, 12, angle_deg)), tab, 1.0)
        c.fill(c.line_mask(rect_points(ccx, ccy + 6, 96, 6, angle_deg)[:2] + rect_points(ccx, ccy + 6, 96, 6, angle_deg)[2:], 2), INK, 0.4)
        c.fill(c.ellipse_mask(ccx + 46, ccy - 22, 6), INK, 0.8)

    c.grain(0.010)
    c.vignette(0.14)
    return c.finish(out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="art_base.png")
    args = parser.parse_args()
    print(render(Path(args.out)))
