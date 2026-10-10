# Drawing recipes

Use the primitives in `scripts/art_kit.py`. Coordinates are 1080-pixel canvas space. Render with
`Canvas(background=..., seed=...)`, compose masks with `fill`, and finish with `finish(path)`.

## Primitives

- `poly_mask(points)`, `ellipse_mask(cx, cy, rx, ry)`, `ring_mask(...)`: shapes as masks.
- `line_mask(points, width, dash=, gap=)`: strokes, dashes for unresolved edges.
- `fill(mask, "#RRGGBB" | array, alpha)`: composite a color or a computed array.
- `sheen(angle, [(pos, "#hex"), ...])`: multi-stop gradient for brass, enamel, paper, lacquer.
- `shadow(mask, dx, dy, blur, alpha)`: cast shadow, with a soft falloff.
- `bevel(mask, dx, dy, "#hex", alpha)`: lit rim, for convincing edges on metal and card.
- `halftone_mask(coverage, cell)`: dot screen driven by a coverage array.
- `hatch_mask(mask, spacing, angle)`: parallel hatching clipped to a shape.
- `text_mask(cx, cy, text, font_path, size)`: sourced text only.
- `radial_glow`, `gradient`, `grain`, `vignette`: atmosphere.
- `arc_points`, `rect_points`, `iso`, `shade`: arcs, rotated rectangles, isometric projection, flat facet shading.

## Recipe: a cast-shadowed metal bar

```python
shaft = c.poly_mask(rect_points(cx, cy, length, 26, angle))
c.shadow(shaft, dx=18, dy=24, blur=12, alpha=0.55)
c.fill(shaft, c.sheen(45, BRASS))
c.bevel(shaft, -2, -3, "#FFF3D0", 0.75)
```

## Recipe: a bell or dome

Use `arc_points(cx, cy, rx, ry, 180, 360)` for the dome, close it with a flared base polygon, and
shade with a horizontal sheen. Add a small base ellipse with its own shadow.

## Recipe: a card with sourced text

Shadow, paper fill, outline, a colored tab strip, then `text_mask` for the label. Keep the font
size so the label fits the card with margin at thumbnail size.

## Recipe: a continuous thread through documents

Build one list of points that passes through each sheet's local coordinates mapped to canvas space,
then draw it twice: a thick colored stroke and a thin highlight on top.

## Pitfalls

- Broadcasting a 2-D mask with a 3-channel gradient needs `[..., 0]` on the gradient first.
- Keep arrays float32 at 2x supersampling; a full-canvas 3-D array can exceed memory.
- Do not place text with an unverified string. Every word must come from `art_text`.
- Avoid reusing one composition in every story. Change the object, medium, and composition.
