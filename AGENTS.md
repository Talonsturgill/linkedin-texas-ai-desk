# Texas Desk automation

This repository owns one product: the daily **Texas Desk** LinkedIn draft for Texas AI Docket.
The finished artifact is an unsent Gmail draft containing copy-ready post text, a permanent image
link, source notes, and an editor report. It never posts to LinkedIn and never sends mail.

## Start here

1. Read `prompts/ROUTINE_PROMPT.txt` and `prompts/texas_desk_routine.md` in full.
2. Read `config/brand.yaml`, `config/sources.yaml`, `config/state.yaml`, and
   `config/rubric.yaml` before researching or writing.
3. Read `references/dossier_schema.md` before creating a dossier.
4. Use `$texas-desk-artwork` only after the post has passed the deterministic copy gate.

The versioned master prompt is authoritative. Keep the scheduler prompt thin so editorial rules
can be reviewed in Git.

## Boundaries that do not bend

- Draft only. Gmail `create_draft` and `update_draft` are allowed. Sending mail is never allowed.
- Never post to LinkedIn, merge a pull request, or push directly to `main`.
- Run artifacts use a unique `codex/texas-desk-YYYY-MM-DD[-NN]` branch. Opening a draft pull
  request is allowed after gates pass.
- Do not modify the sibling TexasAIDocket, TexasAIDispatch, or TexasAIScanner repositories. They
  may be read for public brand and record context only.
- Never store credentials, mailbox addresses, private messages, or connector responses in Git.
  Gmail payloads and delivery receipts live under ignored `.local/` only.
- Every factual claim must trace to a fetched source in `out/desk_dossier.json`. Use a primary
  source plus at least one genuinely independent corroborator for the selected decision.
- Every numeral in post copy must already appear in the dossier. Do not type estimates from
  memory. Publish missing information as a gap.
- No candidate, party, campaign, or ballot-measure advocacy. Do not compare or rank political
  candidates. Public-sector decisions may be covered only as evidence-based accountability
  reporting. Explain sourced tradeoffs neutrally and assess process, implementation, or
  disclosure quality rather than telling readers which political position to support.
- A no-target draft is a correct outcome. It is better than a thin profile or a puff piece.

## Verification

Use Python 3.11 or newer.

```bash
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests -v
python3 scripts/check_config.py
python3 scripts/art_smoke.py
```

`check_config.py` validates the local artwork skill manifest and referenced scripts on both
Mac and Linux. Brand fonts ship in `assets/fonts` with a checksum manifest; art never falls back to
system fonts. No external home-directory validator is required.

For Claude cloud, read `CLAUDE.md` and `config/runtime.json`. Verify required capabilities
before research with `scripts/runtime_check.py`, using the `coded_art` state from
`python3 scripts/art_smoke.py` (it repairs missing Pillow, numpy, or PyYAML from `requirements.txt` and
renders a verified smoke image). A failed render after the two-attempt budget is needs-attention.
Artwork is original code-authored per story (`out/artwork.py`), never a shared template. Use the
attached Git checkout instead of a hard-coded local path. Read each contract once and keep tool output compact.

Newly authored copy, image headlines, and email notes must not contain the whole words
`matter`, `matters`, `mattered`, or `mattering`, case-insensitively. Source evidence and URLs
are exempt. The post, package, and email gates enforce this rule.

For a completed profile run, also execute:

```bash
python3 scripts/check_post.py --post out/final_post.md \
  --dossier out/desk_dossier.json --config config/brand.yaml
python3 scripts/validate_run.py --out-dir out
```

Never describe a skipped check as passed. Inspect the rendered 1080 by 1080 image, not only its
dimensions and metadata.
