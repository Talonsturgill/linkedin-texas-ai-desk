#!/usr/bin/env python3
"""Coded art for the ERCOT Batch Zero verification-before-study decision.

Medium: brass, enamel and graphite linework on an ink ground under overhead light. A queue of
large-load cards waits on a brass rail. The front card is lifted into a brass verification gate.
Cards that do not pass drop off the rail below the gate. A brass seal tab stands on the right
post for the December filing. It names no located property, no campus and no figure; the drawn
objects are conceptual stand-ins for the verified mechanism.
"""

import argparse
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
import math  # noqa: E402

from art_kit import Canvas, rect_points  # noqa: E402

INK = "#0F0C1C"
BLUEBONNET = "#4E5FA8"
BLUEBONNET_HI = "#7F8FD0"
CALICHE = "#E4D8C3"
PAPER = "#EDE6D6"
DUST = "#C9B393"
EMBER = "#E0956A"
BRASS = [(0.0, "#3A2510"), (0.3, "#B8864A"), (0.55, "#FFF3D0"), (0.75, "#C9A063"), (1.0, "#3A2510")]


def brass(c: Canvas, mask, angle: float = 40) -> None:
    c.fill(mask, c.sheen(angle, BRASS))


def card(c: Canvas, cx: float, cy: float, w: float, h: float, angle: float, tab: str) -> None:
    body = c.poly_mask(rect_points(cx, cy, w, h, angle))
    c.shadow(body, dx=6, dy=10, blur=6, alpha=0.5)
    c.fill(body, PAPER, 0.96)
    c.fill(c.poly_mask(rect_points(cx - w * 0.22, cy - h * 0.36, w * 0.42, 10, angle)), tab, 1.0)
    c.fill(c.line_mask(rect_points(cx, cy + 8, w * 0.7, 4, angle)[:2], 3), INK, 0.45)


def render(out: Path) -> Path:
    c = Canvas(background=INK, seed=2026)
    c.radial_glow(560, 420, 520, BLUEBONNET, alpha=0.32, power=1.8)
    c.radial_glow(790, 420, 210, EMBER, alpha=0.10, power=2.0)

    # Brass rail the queue sits on.
    rail = c.poly_mask(rect_points(540, 530, 860, 12, 0))
    c.shadow(rail, dx=4, dy=8, blur=5, alpha=0.5)
    brass(c, rail, 0)

    # Waiting queue: six cards in a row, slightly varied in angle.
    queue_x = [150, 240, 330, 420, 510, 600]
    tabs = [BLUEBONNET, DUST, BLUEBONNET, DUST, BLUEBONNET, DUST]
    for i, (qx, tab) in enumerate(zip(queue_x, tabs)):
        angle = (-4, 3, -2, 5, -3, 2)[i]
        card(c, qx, 484, 62, 80, angle, tab)

    # Front card lifted above the rail toward the gate.
    card(c, 660, 440, 70, 90, -4, BLUEBONNET_HI)

    # Verification gate: two brass posts and a crossbar, with a lit bluebonnet panel.
    left_post = c.poly_mask(rect_points(724, 430, 26, 360, 0))
    right_post = c.poly_mask(rect_points(882, 430, 26, 360, 0))
    crossbar = c.poly_mask(rect_points(803, 262, 184, 26, 0))
    for post in (left_post, right_post, crossbar):
        c.shadow(post, dx=10, dy=14, blur=9, alpha=0.55)
        brass(c, post, 35)
        c.bevel(post, -2, -3, "#FFF3D0", 0.7)
    panel = c.poly_mask(rect_points(803, 430, 132, 340, 0))
    c.fill(panel, c.gradient(90, BLUEBONNET, INK), 0.55)
    c.fill(c.line_mask([(738, 282), (868, 282)], 2, dash=12, gap=8), CALICHE, 0.35)

    # Passing card, now inside the gate, carried through the verification step.
    card(c, 803, 420, 84, 108, 0, BLUEBONNET_HI)
    c.fill(c.line_mask([(760, 448), (800, 478), (856, 418)], 6), EMBER, 0.95)

    # Failed card drops off the rail beneath the gate and is shown displaced.
    card(c, 720, 612, 62, 80, 34, DUST)
    c.fill(c.line_mask(rect_points(720, 612, 74, 92, 34)[:2], 2, dash=8, gap=6), CALICHE, 0.4)

    # Seal tab on the right post stands for the December filing.
    seal = c.ellipse_mask(934, 300, 26)
    brass(c, seal, 25)
    c.fill(c.ellipse_mask(934, 300, 16), INK, 0.85)
    c.fill(c.line_mask([(934, 300), (934, 286)], 3), CALICHE, 0.9)

    c.grain(0.010)
    c.vignette(0.16)
    return c.finish(out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="art_base.png")
    args = parser.parse_args()
    print(render(Path(args.out)))
