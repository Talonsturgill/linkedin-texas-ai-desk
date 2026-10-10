---
name: texas-desk-artwork
description: Author a story-specific coded 1080 by 1080 Texas Desk LinkedIn cover after the copy passes. Write per-story Pillow and numpy artwork code, verify its provenance and variety, then apply exact Texas AI Docket publication type with the deterministic compositor. Use for every profile cover; do not use for research, copy, logos, or unrelated carousels.
---

# Texas Desk Artwork (coded)

Every profile cover is original code-authored editorial art that Claude renders in this
environment. There is no image-generation dependency. The story is carried by the art before the
headline. Historical ImageGen covers remain as honest legacy examples and are never relabeled.

## Workflow

1. Read `out/final_post.md`, `out/desk_dossier.json`, `config/brand.yaml`, and
   `references/acceptance.md`. Pick the decision's physical mechanism and one medium that suits it.
2. Choose a style family, composition, material, light model, and palette from the vocabularies in
   `references/vocabulary.json`. Inspect recent directions before choosing; fetch dated artifact
   branches as the routine requires. The three visual anchors must each bind to a verbatim dossier
   `verified_facts` claim and its fetched source URL. Respect gaps: draw no unverified property,
   campus, output figure, or completed step.
3. Author `out/artwork.py` (per story) from `scripts/art_kit.py` primitives; see
   `references/drawing-recipes.md` and `references/direction-schema.md`. The latter is the complete
   authoring contract; use it instead of reading validator and compositor source on ordinary runs.
   Keep every drawn label a supported sourced date abbreviation, listed in
   `art_text`. Author `out/art_direction.json` (schema_version 2, identity fields, vocabulary values,
   mechanism, three visual anchors, art_text, gaps_respected, ground_tone).
4. Run the one deterministic build: `python3 .agents/skills/texas-desk-artwork/scripts/build_art.py --story-dir out`.
   It renders within the two-attempt budget, updates renderer and dossier hashes, recomposes
   `out/post_image.png` and its sidecar from the direction, writes `out/thumb_300.png`, and resets a
   visual review whose pixels changed. It never marks a check true.
5. Inspect `out/post_image.png` at full size and `out/thumb_300.png`. Record the real review in
   `visual_review` (reviewed SHA-256 values, the two inspection flags, and each check you actually
   verified, with findings that describe the final pixels). Confirm the named style, material,
   composition, and lighting describe those pixels; changing names cannot create variety.
6. Run the gate: `python3 .agents/skills/texas-desk-artwork/scripts/art_gate.py --out-dir out --date <ISO>`
   (validate_run runs the same gate). It recomputes every hash, re-renders `artwork.py`, recomposes
   the final cover and compares pixels, checks anchors, labels and identity against the dossier, and
   enforces variety against committed branch history.

## Hard rules

- New profile covers require `source: coded`. `imagegen` metadata is legacy and valid only for
  historical examples under `examples/`.
- Focal objects stay in the unobstructed band y = 180..680. Compositor dark zones are the top strip
  (0..170) and the headline zone (700 downward); a `light` ground tone adds a stronger top strip
  and darkens from 660 down.
- No arbitrary file-size floor. Polished vector-like art is valid. The ceiling is 5 MB.
- No procedural template is a substitute cover. Each story gets its own `artwork.py`. Reuse
  primitives, never whole scenes, across stories.
- Variety: a new cover must differ from the previous published cover in at least three of six
  dimensions (style family, composition, palette, material, silhouette, light), must not repeat a
  style family or composition from the last 14 days or the last three covers, and must not match any
  of those covers' structure (grayscale gradient hash distance above 40 of 256, and spatial edge
  orientation similarity below 0.92). Fingerprints use only the typography-free band y = 340..540, so
  relabeling or recoloring does not evade the check.
- Two artwork render attempts per ordinary run. An engineering pass may pass `--limit` explicitly.
- Never describe a skipped check as passed. The visual review must be recorded against current
  hashes, so any later change to the image or the base invalidates it.

## Files

- `scripts/art_kit.py` primitives: supersampled canvas, masks, sheen, bevel, shadows, hatch, halftone,
  arcs, rotated rectangles, sourced text.
- `scripts/compose_cover.py` exact typography and compositor bands.
- `scripts/art_gate.py` provenance, anchors, art text, visual review, variety, attempt budget.
- `scripts/build_art.py` the one ordered build: budgeted render, hashes, compose, thumbnail, review reset.
- `scripts/render_art.py` budgeted render plus base verification.
- `scripts/qa_check.py` technical image and sidecar check.
- `references/acceptance.md` visual acceptance checklist (read before reviewing).
- `references/drawing-recipes.md` primitives and recipes (read before drawing).
- `references/visual-system.md` brand palette and Texas-specific rules.
- `references/vocabulary.json` registered style, composition, material and light names with definitions.
- Brand fonts live in the repository's `assets/fonts` with a checksum manifest.
