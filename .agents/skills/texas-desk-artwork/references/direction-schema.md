# Direction contract quick reference

Use this reference to author `out/art_direction.json`; do not reread the validator or compositor
to discover field names on ordinary runs. The build computes hashes and installs the pending
review. Choose the scene yourself from this story's evidence and recent cover history.

Required author fields:

```json
{
  "schema_version": 2,
  "source": "coded",
  "date": "OCTOBER 9TH, 2026",
  "role": "OPERATOR",
  "headline": "A short story-specific headline",
  "place": "COPY selected_subject.place_label EXACTLY",
  "coordinates": "",
  "decision_anchor": "COPY selected_decision.decision_anchor EXACTLY",
  "mechanism": "Describe the sourced decision and the physical action visible in the scene in at least eighty characters.",
  "style_family": "CHOOSE FROM vocabulary.json",
  "composition": "CHOOSE FROM vocabulary.json",
  "palette_key": "a_distinct_descriptive_palette_name",
  "palette": ["#0F0C1C", "#EDE6D6", "#B4664F"],
  "material": "CHOOSE FROM vocabulary.json",
  "silhouette": "Describe the actual arrangement and outlines of the main objects.",
  "light_model": "CHOOSE FROM vocabulary.json",
  "ground_tone": "dark",
  "focal_band": [180, 680],
  "art_text": [],
  "visual_anchors": [],
  "gaps_respected": ["Describe what the evidence does not establish and how the image respects it."],
  "renderer": {"file": "artwork.py", "size": [1080, 1080], "seed": 2026, "supersample": 2}
}
```

Replace every illustrative value, including the date, role, seed, palette, and headline. The date
must equal `art_gate.display_date(dossier['run_date'])`; role is the uppercase dossier
`role_category`. Palette has two to six hex colors. Ground tone is `dark` or `light`.

`visual_anchors` must contain exactly three objects, each with a different zero-based fact index:

```json
{
  "id": "A1",
  "claim_index": 0,
  "claim": "COPY THE COMPLETE verified_facts[0].claim VERBATIM",
  "source_urls": ["COPY A FETCHED URL FROM THAT FACT"],
  "drawn_as": "Describe the concrete object or action that expresses this fact."
}
```

Source URLs must occur both in that fact and in the dossier's fetched source records. Bind claims
by copying their strings programmatically; do not retype or paraphrase them. Empty `art_text` is
correct for a picture with no text inside the scene. The current label gate supports only
month/day abbreviations: an entry such as `{"text":"OCT 31","claim_index":0,
"source_phrase":"October 31st"}` needs that exact source phrase in the referenced fact and the
literal double-quoted label `"OCT 31"` in `artwork.py`. Publication headlines are composed separately.

Run `build_art.py`, then inspect the final cover and thumbnail. Fill in the generated
`visual_review` only after inspection, using the current final and base hashes, all eight checks
listed in `acceptance.md`, and findings describing the actual pixels. Rebuilding changed pixels
resets that review. Do not copy an example's hashes, findings, or passed checks.

Run all commands from the repository root, or use absolute paths. Do not change the working
directory into the skill folder; it makes later relative output paths ambiguous.
