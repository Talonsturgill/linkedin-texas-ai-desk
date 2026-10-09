#!/usr/bin/env python3
"""Primitive kit for coded Texas Desk art: supersampled Pillow masks composed with numpy.

Story artwork lives in each story's own artwork.py. Import these primitives; do not copy
whole scenes between stories. Coordinates are in 1080-pixel canvas space; rendering happens
at SUPERSAMPLE times that resolution and is reduced with LANCZOS in finish().
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SIZE = 1080
SUPERSAMPLE = 2


def color(value: str) -> np.ndarray:
    """Return an RGB float array in 0..1 for a #RRGGBB string."""
    text = value.lstrip("#")
    if len(text) != 6:
        raise ValueError(f"expected #RRGGBB, got {value!r}")
    return np.array([int(text[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32) / 255.0


def shade(base: str, normal: tuple[float, float, float], light: tuple[float, float, float] = (-0.45, -0.6, 0.66),
          ambient: float = 0.42) -> str:
    """Lambert-style facet shading. Returns a #RRGGBB string for a flat face."""
    nx, ny, nz = normal
    length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    lx, ly, lz = light
    light_length = math.sqrt(lx * lx + ly * ly + lz * lz) or 1.0
    lambert = max(0.0, (nx * lx + ny * ly + nz * lz) / (length * light_length))
    rgb = color(base) * (ambient + (1.0 - ambient) * lambert)
    return "#" + "".join(f"{int(round(min(max(v, 0.0), 1.0) * 255)):02X}" for v in rgb)


def iso(x: float, y: float, z: float, origin: tuple[float, float] = (540, 560), scale: float = 1.0) -> tuple[float, float]:
    """Isometric projection of a 3D point onto canvas coordinates."""
    cos30, sin30 = math.cos(math.radians(30)), 0.5
    return (origin[0] + (x - y) * cos30 * scale, origin[1] + (x + y) * sin30 * scale - z * scale)


def arc_points(cx: float, cy: float, rx: float, ry: float, start_deg: float, end_deg: float,
               steps: int = 72) -> list[tuple[float, float]]:
    """Points along an elliptical arc; angles in degrees, 0 at the right, 90 at the bottom."""
    return [(cx + rx * math.cos(math.radians(a)), cy + ry * math.sin(math.radians(a)))
            for a in np.linspace(start_deg, end_deg, steps)]


def rect_points(cx: float, cy: float, w: float, h: float, angle_deg: float = 0.0) -> list[tuple[float, float]]:
    """Corners of a rectangle centered at (cx, cy), rotated by angle_deg."""
    theta = math.radians(angle_deg)
    cos_t, sin_t = math.cos(theta), math.sin(theta)
    corners = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    return [(cx + x * cos_t - y * sin_t, cy + x * sin_t + y * cos_t) for x, y in corners]



class Canvas:
    """A supersampled float RGB canvas that composes masks, gradients, shadows and texture."""

    def __init__(self, size: int = SIZE, background: str = "#08060F", supersample: int = SUPERSAMPLE,
                 seed: int = 1701) -> None:
        self.size = size
        self.ss = supersample
        self.n = size * supersample
        self.rng = np.random.default_rng(seed)
        self.img = np.empty((self.n, self.n, 3), dtype=np.float32)
        self.img[:] = color(background)

    # ----- coordinate helpers -------------------------------------------------
    def _pts(self, points):
        return [(float(x) * self.ss, float(y) * self.ss) for x, y in points]

    def _blank(self) -> Image.Image:
        return Image.new("L", (self.n, self.n), 0)

    def _to_mask(self, image: Image.Image) -> np.ndarray:
        return np.asarray(image, dtype=np.float32) / 255.0

    # ----- mask builders -----------------------------------------------------
    def poly_mask(self, points) -> np.ndarray:
        image = self._blank()
        ImageDraw.Draw(image).polygon(self._pts(points), fill=255)
        return self._to_mask(image)

    def ellipse_mask(self, cx: float, cy: float, rx: float, ry: float | None = None) -> np.ndarray:
        ry = rx if ry is None else ry
        image = self._blank()
        box = [(cx - rx) * self.ss, (cy - ry) * self.ss, (cx + rx) * self.ss, (cy + ry) * self.ss]
        ImageDraw.Draw(image).ellipse(box, fill=255)
        return self._to_mask(image)

    def line_mask(self, points, width: float, dash: float | None = None, gap: float | None = None) -> np.ndarray:
        image = self._blank()
        draw = ImageDraw.Draw(image)
        for (x0, y0), (x1, y1) in zip(points[:-1], points[1:]):
            if not dash:
                draw.line(self._pts([(x0, y0), (x1, y1)]), fill=255, width=max(1, int(width * self.ss)))
                continue
            length = math.hypot(x1 - x0, y1 - y0) or 1.0
            step = dash + (gap or dash)
            t = 0.0
            while t < length:
                t_end = min(t + dash, length)
                a = (x0 + (x1 - x0) * t / length, y0 + (y1 - y0) * t / length)
                b = (x0 + (x1 - x0) * t_end / length, y0 + (y1 - y0) * t_end / length)
                draw.line(self._pts([a, b]), fill=255, width=max(1, int(width * self.ss)))
                t += step
        return self._to_mask(image)

    def hatch_mask(self, mask: np.ndarray, spacing: float, angle_deg: float, width: float = 1.0) -> np.ndarray:
        """Parallel hatch lines clipped to an existing mask."""
        diagonal = self.size * 1.5
        theta = math.radians(angle_deg)
        dx, dy = math.cos(theta), math.sin(theta)
        nx, ny = -dy, dx
        lines = np.zeros_like(mask)
        offset = -diagonal
        while offset < diagonal:
            cx, cy = self.size / 2 + nx * offset, self.size / 2 + ny * offset
            points = [(cx - dx * diagonal, cy - dy * diagonal), (cx + dx * diagonal, cy + dy * diagonal)]
            lines = np.maximum(lines, self.line_mask(points, width))
            offset += spacing
        return lines * mask

    def halftone_mask(self, mask: np.ndarray, cell: float) -> np.ndarray:
        """Dot screen whose dot radius follows the local coverage of a source mask."""
        image = self._blank()
        draw = ImageDraw.Draw(image)
        cell_px = cell * self.ss
        step = max(2, int(cell_px))
        for gy in range(0, self.n, step):
            for gx in range(0, self.n, step):
                coverage = float(mask[min(gy + step // 2, self.n - 1), min(gx + step // 2, self.n - 1)])
                if coverage < 0.02:
                    continue
                radius = 0.5 * cell_px * math.sqrt(coverage)
                draw.ellipse([gx + step / 2 - radius, gy + step / 2 - radius,
                              gx + step / 2 + radius, gy + step / 2 + radius], fill=255)
        return self._to_mask(image)

    # ----- compositing -------------------------------------------------------
    def fill(self, mask: np.ndarray, fill, alpha: float = 1.0) -> None:
        """Composite a color (#RRGGBB or HxWx3 array) through a mask."""
        source = color(fill) if isinstance(fill, str) else fill
        weight = (mask * alpha)[..., None]
        self.img = self.img * (1.0 - weight) + source * weight

    def gradient(self, angle_deg: float, start: str, end: str, mask: np.ndarray | None = None) -> np.ndarray:
        """Linear gradient across the canvas at an angle. Returns an HxWx3 array."""
        theta = math.radians(angle_deg)
        ys, xs = np.mgrid[0:self.n, 0:self.n].astype(np.float32)
        projection = (xs * math.cos(theta) + ys * math.sin(theta)) / self.n
        t = (projection - projection.min()) / max(1e-6, float(projection.max() - projection.min()))
        a, b = color(start), color(end)
        return (a * (1 - t)[..., None] + b * t[..., None]).astype(np.float32)

    def radial_glow(self, cx: float, cy: float, radius: float, fill: str, alpha: float = 0.6,
                    power: float = 2.2) -> None:
        ys, xs = np.mgrid[0:self.n, 0:self.n].astype(np.float32)
        distance = np.sqrt((xs - cx * self.ss) ** 2 + (ys - cy * self.ss) ** 2) / (radius * self.ss)
        weight = np.clip(1.0 - distance, 0.0, 1.0) ** power * alpha
        self.img = self.img * (1 - weight[..., None]) + color(fill) * weight[..., None]

    def blur(self, mask: np.ndarray, radius: float) -> np.ndarray:
        image = Image.fromarray((np.clip(mask, 0, 1) * 255).astype(np.uint8), "L")
        return self._to_mask(image.filter(ImageFilter.GaussianBlur(radius * self.ss)))

    def shadow(self, mask: np.ndarray, dx: float = 14, dy: float = 22, blur: float = 14,
               fill: str = "#000000", alpha: float = 0.5) -> None:
        shifted = np.roll(np.roll(mask, int(dy * self.ss), axis=0), int(dx * self.ss), axis=1)
        self.fill(self.blur(shifted, blur), fill, alpha)

    def outline(self, mask: np.ndarray, width: float, fill: str, alpha: float = 1.0) -> None:
        grown = self.blur(mask, width) > 0.5
        edge = grown & ~(self.blur(mask, width * 0.5) > 0.5)
        self.fill(edge.astype(np.float32), fill, alpha)

    def sheen(self, angle_deg: float, stops: list[tuple[float, str]]) -> np.ndarray:
        """Multi-stop gradient across the canvas: stops are (position 0..1, #RRGGBB), e.g. brass or enamel."""
        theta = math.radians(angle_deg)
        ys, xs = np.mgrid[0:self.n, 0:self.n].astype(np.float32)
        projection = (xs * math.cos(theta) + ys * math.sin(theta)) / self.n
        t = (projection - projection.min()) / max(1e-6, float(projection.max() - projection.min()))
        positions = [p for p, _ in stops]
        channels = [np.array([color(h)[k] for _, h in stops], dtype=np.float32) for k in range(3)]
        return np.stack([np.interp(t, positions, channel) for channel in channels], axis=-1).astype(np.float32)

    def shift(self, mask: np.ndarray, dx: float, dy: float) -> np.ndarray:
        return np.roll(np.roll(mask, int(dy * self.ss), axis=0), int(dx * self.ss), axis=1)

    def bevel(self, mask: np.ndarray, dx: float, dy: float, fill: str, alpha: float = 0.8, blur: float = 1.2) -> None:
        """Lit rim on the side of a shape facing (-dx, -dy): mask minus its shifted copy, softened."""
        rim = np.clip(mask - self.shift(mask, dx, dy), 0.0, 1.0)
        self.fill(self.blur(rim, blur), fill, alpha)

    def ring_mask(self, cx: float, cy: float, rx: float, ry: float, inner_rx: float, inner_ry: float) -> np.ndarray:
        return np.clip(self.ellipse_mask(cx, cy, rx, ry) - self.ellipse_mask(cx, cy, inner_rx, inner_ry), 0.0, 1.0)

    def text_mask(self, cx: float, cy: float, text: str, font_path: str, size: float) -> np.ndarray:
        """Centered text rendered at supersample resolution. Use only for dossier-sourced strings."""
        from PIL import ImageFont

        font = ImageFont.truetype(font_path, int(size * self.ss))
        image = self._blank()
        ImageDraw.Draw(image).text((cx * self.ss, cy * self.ss), text, font=font, fill=255, anchor="mm")
        return self._to_mask(image)

    # ----- finishing ---------------------------------------------------------
    def grain(self, amount: float = 0.012) -> None:
        noise = self.rng.normal(0.0, amount, (self.n, self.n, 1)).astype(np.float32)
        self.img = np.clip(self.img + noise, 0.0, 1.0)

    def vignette(self, strength: float = 0.25) -> None:
        ys, xs = np.mgrid[0:self.n, 0:self.n].astype(np.float32)
        r = np.sqrt(((xs - self.n / 2) / (self.n / 2)) ** 2 + ((ys - self.n / 2) / (self.n / 2)) ** 2)
        self.img = self.img * (1 - strength * np.clip(r - 0.6, 0, 1)[..., None] ** 1.5)

    def to_image(self) -> Image.Image:
        pixels = (np.clip(self.img, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)
        return Image.fromarray(pixels, "RGB").resize((self.size, self.size), Image.Resampling.LANCZOS)

    def finish(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.to_image().save(path, "PNG", optimize=True)
        return path


def smoke_render(path: Path) -> tuple[int, int]:
    """Tiny end-to-end render used by preflight: one gradient, one facet, one ring."""
    canvas = Canvas(size=128, background="#08060F", supersample=2)
    canvas.img = canvas.gradient(60, "#191530", "#E0956A")
    face = canvas.poly_mask([(20, 100), (64, 70), (108, 100), (64, 124)])
    canvas.shadow(face, dx=4, dy=6, blur=3, alpha=0.5)
    canvas.fill(face, shade("#B4664F", (0.0, -1.0, 0.0)))
    canvas.fill(canvas.line_mask([(10, 20), (118, 20)], 2), "#F6F1E4", 0.8)
    image = canvas.to_image()
    image.save(path, "PNG")
    return image.size
