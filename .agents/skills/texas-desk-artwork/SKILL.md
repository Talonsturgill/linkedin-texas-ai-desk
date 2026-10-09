---
name: texas-desk-artwork
description: Create the story-specific 1080 by 1080 Texas Desk LinkedIn cover after a verified post is final. Use built-in ImageGen for the original artwork, then apply the exact Texas AI Docket wordmark, kicker, headline, date, and place with the deterministic compositor. Do not use for research, post writing, logos, or unrelated TexasAIDocket carousel work.
---

# Texas Desk Artwork

Create one original editorial image that illustrates the selected decision. The final cover must
be a real generated raster composition. Missing ImageGen or two failed attempts ends the run
as needs-attention; a procedural template does not satisfy the current delivery contract.

## Inputs

Read these before generating:

- `out/final_post.md`
- `out/desk_dossier.json`
- `config/brand.yaml`

The dossier supplies the story, location, verified visual facts, and headline constraints. Do not
invent infrastructure, insignia, documents, people, dollar figures, or place-specific details.

## Primary path

1. Write `out/image_prompt.txt` as a compact production brief using this order:

   - `Use case: stylized-concept`
   - `Asset type: square LinkedIn editorial cover background`
   - `Primary request:` one visual metaphor for the verified decision
   - `Scene/backdrop:` the dossier's real Texas region and material world
   - `Subject:` the decision's mechanism, consequence, or physical setting
   - `Style/medium:` one specific editorial medium
   - `Composition/framing:` one focal point, generous quiet bands at top and bottom for later type
   - `Lighting/mood:` matched to the evidence, not generic drama
   - `Color palette:` two to six story-appropriate inks grounded in the Texas AI Docket palette
   - `Constraints:` square, no words, no letters, no numbers, no logos, no watermarks, no UI,
     no generated portrait or likeness of the profiled person
   - `Avoid:` boots, cowboy hats, longhorns, tourist Texas silhouettes, decorative oil derricks,
     generic glowing brains, circuit-board faces, handshakes, and red used as decoration

2. Invoke the built-in `$imagegen` path with that brief. Generate a brand-new square raster image.
   Do not use CLI or an API key. Save or copy the selected result into `out/art_base.png`.
3. Inspect `out/art_base.png` at full size. Reject extra text, logos, watermarks, false geography,
   visual clichés, distorted people, or a weak focal hierarchy. Make one targeted regeneration
   when a concrete defect is visible. A second failed built-in generation ends the primary path.
4. Keep the image itself free of typography. Exact copy is added deterministically:

   ```bash
   python3 .agents/skills/texas-desk-artwork/scripts/compose_cover.py \
     --base out/art_base.png \
     --headline "<one or two short lines>" \
     --role "<FOUNDER|OPERATOR|PUBLIC|RESEARCH>" \
     --date "<MONTH DTH, YYYY>" \
     --place "<REAL PLACE OR STATEWIDE>" \
     --coords "<VERIFIED COORDINATES OR EMPTY>" \
     --prompt-file out/image_prompt.txt \
     --source imagegen \
     --out out/post_image.png
   ```

5. Inspect the composed cover at full size and as a 300-pixel thumbnail. The headline must be
   exact and legible, the artwork must remain the focal event, and the mark must read as quiet
   publication furniture.
6. Run the technical gate:

   ```bash
   python3 .agents/skills/texas-desk-artwork/scripts/qa_check.py \
     --image out/post_image.png --date "<MONTH DTH, YYYY>" --column "TEXAS DESK"
   ```

## Unavailable tool or failed generation

Stop as needs-attention when the built-in tool is unavailable or two attempts fail. Report the
actual observation and attempt count in the unsent status draft. Do not claim two failed calls
when the tool was absent. The legacy fallback renderer is retained for historical fixtures only;
never use it to satisfy the current generated-artwork requirement.

For the brand rationale and visual exclusions, read
[`references/visual-system.md`](references/visual-system.md).
