#!/usr/bin/env python3
"""Coded art for the Scaffold seed-funding and cross-system coordination decision.

Historical visual acceptance example, not current news. Medium: three floating ink-on-paper sheets
over a deep panel. The back sheet is a construction floor plan, the middle sheet is a purchase
order grid, and the front sheet is a schedule with an open bar. One continuous copper thread runs
through all three, so existing documents are connected rather than replaced. The schedule bar
ends in dashes because the dossier sets no completion deadline.
"""

import argparse
import math
import sys
from pathlib import Path


def _kit() -> None:
    import os

    override = os.environ.get("TEXAS_DESK_KIT")
    if override:
        sys.path.insert(0, override)
        return
    for parent in Path(__file__).resolve().parents:
        candidate = parent / ".agents/skills/texas-desk-artwork/scripts"
        if candidate.is_dir():
            sys.path.insert(0, str(candidate))
            return
    raise RuntimeError("texas-desk-artwork scripts not found")


_kit()
from art_kit import Canvas, rect_points  # noqa: E402

INK = "#0F0C1C"
PAPER = "#EDE6D6"
EMBER = "#B4664F"
BLUE = "#4E5FA8"
COPPER = "#E0956A"


class Sheet:
    """A sheet in local coordinates (origin at its center), placed by angle and center."""

    def __init__(self, c: Canvas, cx: float, cy: float, angle: float, w: float = 360, h: float = 240):
        self.c, self.cx, self.cy, self.angle, self.w, self.h = c, cx, cy, angle, w, h
        theta = math.radians(angle)
        self.cos, self.sin = math.cos(theta), math.sin(theta)
        mask = c.poly_mask(rect_points(cx, cy, w, h, angle))
        c.shadow(mask, dx=14, dy=20, blur=12, alpha=0.6)
        c.fill(mask, PAPER, 0.97)
        c.outline(mask, 2.0, INK, 0.9)

    def at(self, lx: float, ly: float) -> tuple[float, float]:
        return (self.cx + lx * self.cos - ly * self.sin, self.cy + lx * self.sin + ly * self.cos)

    def line(self, points, width: float = 4, color: str = INK, alpha: float = 1.0, dash=None, gap=None) -> None:
        mapped = [self.at(x, y) for x, y in points]
        self.c.fill(self.c.line_mask(mapped, width, dash=dash, gap=gap), color, alpha)

    def box(self, x0: float, y0: float, x1: float, y1: float, width: float = 4, color: str = INK) -> None:
        self.line([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], width, color)

    def fill_box(self, x0: float, y0: float, x1: float, y1: float, color: str, alpha: float = 1.0) -> None:
        mapped = [self.at(x, y) for x, y in [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]]
        self.c.fill(self.c.poly_mask(mapped), color, alpha)


def render(out: Path) -> Path:
    c = Canvas(background="#191530", seed=2309)
    c.img = c.gradient(70, "#191530", "#2B2447")
    c.radial_glow(540, 380, 460, BLUE, alpha=0.35, power=1.6)

    # Back sheet: construction floor plan (walls, rooms, a door swing, a dimension run).
    plan = Sheet(c, 350, 330, -8)
    plan.box(-160, -100, 160, 100, width=6)
    plan.line([(-60, -100), (-60, 20), (20, 20), (20, -100)], width=5)
    plan.line([(-160, 20), (-60, 20)], width=5)
    plan.line([(20, 20), (160, 20)], width=5)
    plan.line([(100, -100), (100, 100)], width=4, dash=10, gap=7)
    plan.line([(-160, 60), (-100, 60)], width=3, color=BLUE)
    plan.fill_box(-40, -60, 0, -20, BLUE, 0.35)

    # Middle sheet: purchase-order grid, five rows of line items, first row inked as the order.
    po = Sheet(c, 560, 420, 5)
    for i in range(6):
        x = -150 + i * 60
        po.line([(x, -100), (x, 100)], width=4)
    for j in range(5):
        y = -100 + j * 40
        po.line([(-150, y), (150, y)], width=4)
    po.fill_box(-150, -100, 150, -60, EMBER, 0.85)
    po.fill_box(-150, -20, -90, 0, BLUE, 0.4)
    po.fill_box(30, 20, 90, 60, BLUE, 0.4)

    # Front sheet: schedule as gantt bars; the last bar runs out with no completion marker.
    sched = Sheet(c, 730, 290, -3)
    for index, (start, end) in enumerate([(-150, -20), (-60, 60), (-100, 120)]):
        y = -80 + index * 50
        sched.fill_box(start, y - 12, end, y + 12, INK, 0.9)
    sched.line([(40, 20), (150, 20)], width=10, color=INK, dash=14, gap=12)
    sched.line([(-150, 75), (150, 75)], width=3, color=INK)
    for x in (-150, -100, -50, 0, 50, 100, 150):
        sched.line([(x, 65), (x, 85)], width=3)

    # One continuous copper thread through plan, purchase order and schedule.
    thread = [plan.at(60, -40), plan.at(-80, 0), plan.at(-120, 60)]
    thread += [po.at(-110, -80), po.at(-20, -60), po.at(60, -20), po.at(110, 40)]
    thread += [sched.at(-100, -80), sched.at(-80, -30), sched.at(-20, 10), sched.at(40, 20)]
    c.fill(c.line_mask(thread, 7), COPPER, 0.95)
    c.fill(c.line_mask(thread, 2.5), "#FFF3D0", 0.9)

    c.grain(0.010)
    c.vignette(0.12)
    return c.finish(out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="art_base.png")
    args = parser.parse_args()
    print(render(Path(args.out)))
