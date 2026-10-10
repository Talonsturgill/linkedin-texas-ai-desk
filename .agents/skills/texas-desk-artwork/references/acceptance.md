# Visual acceptance checklist

A cover is accepted only when every item below is true and you verified it on the rendered image.
These are the same bars for every story.

1. **Distinctive material object.** The art shows a recognizable physical thing with its own
   material (brass, lacquer, paper, dot-screen, plan linework). Sparse rectangles with a caption in
   the headline do not pass.
2. **Visible story action.** The image shows the decision's mechanism happening: a date tab
   spanning an unresolved gap, a key engaging a sector, a thread through documents. A reader should
   see the action before reading any words.
3. **Art carries the story before the headline.** Remove the headline mentally: the picture alone
   still names the mechanism.
4. **Sourced text only.** Any word or numeral in the art is a dated or named string from a dossier
   fact and appears in `art_text` with its `claim_index` and `source_phrase`.
5. **Respect the gaps.** Draw nothing the dossier does not establish: no completed campus, no
   located property, no unverified figures, no finished step where the dossier says conditional.
6. **Focal band.** The focal object sits within y = 180..680.
7. **Contrast at thumbnail size.** At 300 px the main objects and any sourced text stay legible.
   Thin faded strokes are not enough; use strong ink or solid form.
8. **Distinct from neighbours.** The cover differs from the other covers in this batch and from
   recent history in at least three dimensions (see SKILL.md).
9. **Political neutrality and editorial safety.** No candidate, party, campaign, or ballot
   imagery. No flags, badges, or emblems that imply endorsement.
10. **Clean rendering.** 2x supersampling, no clipping, no aliasing artifacts, no blank regions by
    accident.

Record the result in `visual_review.checks` with exactly these keys:
`anchors_visible`, `focal_object_in_180_680_band`, `distinctive_material_object`,
`visible_story_action`, `art_carries_story_before_headline`,
`no_generic_server_or_texas_outline`, `no_clipping_or_artifacts`, `decision_readable`.
Set `full_size_checked` and `thumbnail_300_checked` only after viewing both.
