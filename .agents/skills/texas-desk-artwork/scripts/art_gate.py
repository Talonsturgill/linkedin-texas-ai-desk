#!/usr/bin/env python3
"""Coded-art provenance, consistency, label, visual-review, and variety gate for Texas Desk covers.

The gate recomputes rather than trusting stored booleans: file hashes, the base image (by
re-rendering artwork.py), the final cover (by recomposing it from the bound base, direction
manifest, and dossier, then comparing pixels), anchors and labels against the dossier, and variety
against committed dated history read with git. A failing git read is an error, never empty history.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import math
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]
for path in (HERE, ROOT / "scripts"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

SIZE = 1080
MAX_BYTES = 5 * 1024 * 1024
FINGERPRINT_BAND = (0, 340, 1080, 540)  # no overlay, no typography: see compose_cover.py
DHASH_NEAR = 40  # of 256 bits; at or below this distance the structure is the same picture
EDGE_NEAR = 0.92  # cosine of spatial orientation histograms; at or above this the structure matches
WINDOW_DAYS = 14
RECENT_COVERS = 3
MIN_CHANGED_DIMENSIONS = 3
ATTEMPT_LIMIT = 2
DIMENSIONS = ("style_family", "composition", "palette_key", "material", "silhouette", "light_model")
VOCABULARY = json.loads((HERE.parent / "references/vocabulary.json").read_text(encoding="utf-8"))
STYLE_FAMILIES = set(VOCABULARY["style_families"])
COMPOSITIONS = set(VOCABULARY["compositions"])
MATERIALS = set(VOCABULARY["materials"])
LIGHT_MODELS = set(VOCABULARY["light_models"])
ROLES = {"FOUNDER", "OPERATOR", "PUBLIC", "RESEARCH"}
REQUIRED_META = ["date", "kicker", "role", "headline", "place", "source", "base_sha256",
                 "renderer_sha256", "dossier_sha256", "style_family", "composition", "palette",
                 "material", "silhouette", "light_model", "seed"]
CHECK_KEYS = ("anchors_visible", "focal_object_in_180_680_band", "distinctive_material_object",
              "visible_story_action", "art_carries_story_before_headline",
              "no_generic_server_or_texas_outline", "no_clipping_or_artifacts", "decision_readable")
REF_PATTERN = re.compile(r"refs/remotes/origin/codex/texas-desk-(\d{4}-\d{2}-\d{2})(?:-(\d+))?")
HEX = re.compile(r"#[0-9A-Fa-f]{6}")
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"]
PHRASE = re.compile(r"^(%s) (\d{1,2})(st|nd|rd|th)$" % "|".join(MONTHS))


class HistoryError(RuntimeError):
    """Raised when committed history cannot be read; the gate must fail closed."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


# ----- dates and labels --------------------------------------------------------
def display_date(iso: str) -> str:
    """ISO run date to publication form, e.g. 2026-10-07 to OCTOBER 7TH, 2026."""
    day = dt.date.fromisoformat(iso)
    suffix = "TH" if 11 <= day.day % 100 <= 13 else {1: "ST", 2: "ND", 3: "RD"}.get(day.day % 10, "TH")
    return f"{MONTHS[day.month - 1].upper()} {day.day}{suffix}, {day.year}"


def expected_label(phrase: str) -> str | None:
    """Only month-and-day phrases may be abbreviated in art: SEP 30 for September 30th."""
    match = PHRASE.fullmatch(phrase.strip())
    if not match:
        return None
    return f"{match.group(1)[:3].upper()} {int(match.group(2))}"


# ----- fingerprints ----------------------------------------------------------
def fingerprint(image: Image.Image) -> dict:
    """Structure-only fingerprint of the typography-free band: gradient hash and spatial edges."""
    band = image.convert("L").crop(FINGERPRINT_BAND)
    small = np.asarray(band.resize((17, 16), Image.Resampling.LANCZOS), dtype=np.int16)
    bits = (small[:, 1:] > small[:, :-1]).flatten()
    dhash = "".join("1" if b else "0" for b in bits)
    edge_image = np.asarray(band.resize((192, 36), Image.Resampling.LANCZOS), dtype=float)
    gx = edge_image[1:, 1:] - edge_image[1:, :-1]
    gy = edge_image[1:, 1:] - edge_image[:-1, 1:]
    magnitude = np.hypot(gx, gy)
    angle = np.mod(np.arctan2(gy, gx), math.pi)
    cells = []
    for row in range(2):
        for column in range(4):
            block = np.s_[row * 18:(row + 1) * 18, column * 48:(column + 1) * 48]
            histogram, _ = np.histogram(angle[block], bins=12, range=(0, math.pi), weights=magnitude[block])
            cells.append(histogram)
    flat = np.concatenate(cells)
    total = float(flat.sum())
    flat = (flat / total).tolist() if total > 0 else [0.0] * 96
    return {"dhash": dhash, "edge": [round(v, 6) for v in flat]}


def dhash_distance(a: str, b: str) -> int:
    return sum(x != y for x, y in zip(a, b))


def edge_similarity(a: list[float], b: list[float]) -> float:
    left, right = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
    return float(left @ right / denominator) if denominator else 0.0


# ----- history -----------------------------------------------------------------
def _entry(*, ref: str, date: str, png: bytes, meta: dict | None, manifest: dict | None) -> dict:
    meta = meta or {}
    manifest = manifest or {}
    fp = fingerprint(Image.open(io.BytesIO(png)))
    values = {key: manifest.get(key, meta.get(key)) for key in DIMENSIONS}
    legacy = meta.get("source") == "imagegen" or not manifest
    return {"ref": ref, "date": date, "suffix": 0, "legacy": bool(legacy), **values, **fp}


def _git(repo: Path, *args: str, required: bool = False) -> bytes | None:
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True)
    if result.returncode != 0:
        if required:
            raise HistoryError(f"git {' '.join(args)} failed: {result.stderr.decode(errors='replace').strip()}")
        return None
    return result.stdout


def _sort_key(entry: dict) -> tuple[str, int]:
    return entry["date"], int(entry["suffix"])


def load_history(repo: Path, run_date: str, exclude_branch: str | None = None) -> list[dict]:
    """Every committed dated Texas Desk cover on origin dated on or before run_date.

    Same-day earlier runs with numeric suffixes (-2 ... -10) are included and sorted numerically.
    The current run's branch is excluded by name. Any failing git read raises HistoryError.
    """
    if exclude_branch is None:
        current = _git(repo, "symbolic-ref", "--quiet", "--short", "HEAD")
        exclude_branch = current.decode().strip() if current else None
    refs = _git(repo, "for-each-ref", "--format=%(refname)",
                "refs/remotes/origin/codex/texas-desk-*", required=True).decode()
    entries = []
    for ref in refs.split():
        match = REF_PATTERN.fullmatch(ref)
        if not match:
            continue
        date = match.group(1)
        branch = ref.removeprefix("refs/remotes/origin/")
        if date > run_date or branch == exclude_branch:
            continue
        # Honest no-target artifacts have a dossier and deliberately have no cover.
        dossier_raw = _git(repo, "show", f"{ref}:out/desk_dossier.json")
        if dossier_raw:
            try:
                historical_dossier = json.loads(dossier_raw)
            except (ValueError, UnicodeError) as exc:
                raise HistoryError(f"invalid history dossier at {ref}") from exc
            if historical_dossier.get("no_target_this_cycle") is True:
                continue
        png = _git(repo, "show", f"{ref}:out/post_image.png", required=True)
        meta_raw = _git(repo, "show", f"{ref}:out/post_image.png.meta.json")
        manifest_raw = _git(repo, "show", f"{ref}:out/art_direction.json")
        entry = _entry(
            ref=ref, date=date, png=png,
            meta=json.loads(meta_raw) if meta_raw else None,
            manifest=json.loads(manifest_raw) if manifest_raw else None,
        )
        entry["suffix"] = int(match.group(2) or 1)
        entries.append(entry)
    return sorted(entries, key=_sort_key)


def select_history(entries: list[dict], run_date: str) -> tuple[list[dict], dict | None]:
    """Last 14 days plus the most recent published covers; returns (compared set, previous cover)."""
    run = dt.date.fromisoformat(run_date)
    ordered = sorted((e for e in entries if e["date"] <= run_date), key=_sort_key)
    windowed = [e for e in ordered if (run - dt.date.fromisoformat(e["date"])).days <= WINDOW_DAYS]
    recent = ordered[-RECENT_COVERS:]
    selected = {e["ref"]: e for e in windowed + recent}
    previous = ordered[-1] if ordered else None
    return list(selected.values()), previous


def compare(candidate: dict, history: list[dict], previous: dict | None) -> list[str]:
    errors = []
    if previous is not None:
        changed = [key for key in DIMENSIONS if candidate.get(key) != previous.get(key)]
        if len(changed) < MIN_CHANGED_DIMENSIONS:
            errors.append(
                f"variety: only {len(changed)} dimensions differ from previous cover {previous['ref']}; "
                f"need {MIN_CHANGED_DIMENSIONS}"
            )
    for item in history:
        name = item["ref"]
        if candidate.get("style_family") and candidate["style_family"] == item.get("style_family"):
            errors.append(f"variety: style family repeats {name}")
        if candidate.get("composition") and candidate["composition"] == item.get("composition"):
            errors.append(f"variety: composition repeats {name}")
        distance = dhash_distance(candidate["dhash"], item["dhash"])
        if distance <= DHASH_NEAR:
            errors.append(f"variety: art structure is near-identical to {name} (dhash distance {distance})")
        similarity = edge_similarity(candidate["edge"], item["edge"])
        if similarity >= EDGE_NEAR:
            errors.append(f"variety: edge structure matches {name} (similarity {similarity:.3f})")
    return errors


# ----- provenance and consistency --------------------------------------------
def _dossier_urls(dossier: dict) -> set[str]:
    decision = dossier.get("selected_decision", {})
    urls = {decision.get("primary_source", {}).get("url", "")}
    urls.update(c.get("url", "") for c in decision.get("corroborating_sources", []))
    for fact in dossier.get("verified_facts", []):
        urls.update(fact.get("source_urls", []))
    return {u for u in urls if u}


def validate_anchors(manifest: dict, dossier: dict) -> list[str]:
    errors = []
    anchors = manifest.get("visual_anchors")
    if not isinstance(anchors, list) or len(anchors) != 3:
        return ["manifest needs exactly three visual_anchors"]
    facts = dossier.get("verified_facts", [])
    urls = _dossier_urls(dossier)
    seen_index: set[int] = set()
    seen_ids: set[str] = set()
    for anchor in anchors:
        anchor_id = anchor.get("id")
        if not anchor_id or anchor_id in seen_ids:
            errors.append("visual anchors need unique ids")
            continue
        seen_ids.add(anchor_id)
        index = anchor.get("claim_index")
        if not isinstance(index, int) or not 0 <= index < len(facts):
            errors.append(f"anchor {anchor_id} does not reference a dossier fact")
            continue
        if index in seen_index:
            errors.append(f"anchor {anchor_id} repeats dossier fact {index}")
        seen_index.add(index)
        fact = facts[index]
        if anchor.get("claim") != fact.get("claim"):
            errors.append(f"anchor {anchor_id} claim is not verbatim dossier fact {index}")
        fact_urls = set(fact.get("source_urls", []))
        requested = set(anchor.get("source_urls", []))
        if not requested or not requested <= fact_urls or not requested <= urls:
            errors.append(f"anchor {anchor_id} source URLs are not dossier-fetched sources for that fact")
        if not str(anchor.get("drawn_as", "")).strip():
            errors.append(f"anchor {anchor_id} needs a drawn_as description")
    return errors


def validate_art_text(manifest: dict, dossier: dict, artwork_source: str) -> list[str]:
    """Each drawn label must be the supported abbreviation of a dossier phrase and appear in artwork.py."""
    errors = []
    facts = dossier.get("verified_facts", [])
    for entry in manifest.get("art_text", []):
        text = str(entry.get("text", ""))
        index = entry.get("claim_index")
        phrase = str(entry.get("source_phrase", ""))
        if not isinstance(index, int) or not 0 <= index < len(facts):
            errors.append(f"art text {text!r} does not reference a dossier fact")
            continue
        if phrase not in facts[index].get("claim", ""):
            errors.append(f"art text {text!r} source phrase is not verbatim in dossier fact {index}")
        if expected_label(phrase) != text:
            errors.append(f"art text {text!r} is not the supported label for {phrase!r}")
        if f'"{text}"' not in artwork_source:
            errors.append(f"art text {text!r} is not drawn by artwork.py")
    return errors


def validate_identity(manifest: dict, meta: dict, dossier: dict) -> list[str]:
    """Headline, role, place, date, coordinates and decision anchor must agree across all records."""
    from prose_rules import check_prose

    errors = []
    subject = dossier.get("selected_subject", {})
    decision = dossier.get("selected_decision", {})
    for key in ("headline", "role", "place", "date", "coordinates"):
        if manifest.get(key) != meta.get(key):
            errors.append(f"manifest and metadata disagree on {key}")
    if meta.get("role") not in ROLES:
        errors.append("role must be FOUNDER, OPERATOR, PUBLIC, or RESEARCH")
    if meta.get("role") != str(subject.get("role_category", "")).upper():
        errors.append("role does not match the dossier role_category")
    if meta.get("place") != subject.get("place_label"):
        errors.append("place does not match the dossier place_label")
    if meta.get("date") != display_date(str(dossier.get("run_date", ""))):
        errors.append("date does not match the dossier run_date in publication form")
    if manifest.get("decision_anchor") != decision.get("decision_anchor"):
        errors.append("decision_anchor does not match the dossier")
    errors.extend(check_prose(str(meta.get("headline", ""))))
    return errors


def recompute_base(out_dir: Path) -> str | None:
    """Re-render artwork.py in isolated mode and return the new base hash, or None on failure."""
    with tempfile.TemporaryDirectory() as temporary:
        target = Path(temporary) / "base.png"
        try:
            result = subprocess.run(
                [sys.executable, "-I", "artwork.py", "--out", str(target)],
                cwd=out_dir, capture_output=True, timeout=240,
            )
        except subprocess.TimeoutExpired:
            return None
        if result.returncode != 0 or not target.is_file():
            return None
        return sha256_file(target)


def recompose_matches(out_dir: Path, manifest: dict) -> str | None:
    """Recompose the final cover from bound inputs and compare pixels. Returns an error or None."""
    import compose_cover

    with tempfile.TemporaryDirectory() as temporary:
        target = Path(temporary) / "final.png"
        compose_cover.compose(
            base_path=out_dir / "art_base.png", headline=manifest["headline"], role=manifest["role"],
            date=manifest["date"], place=manifest["place"], coords=manifest.get("coordinates", ""),
            source="coded", out_path=target, art_direction=out_dir / "art_direction.json",
            renderer=out_dir / "artwork.py", dossier=out_dir / "desk_dossier.json",
        )
        rebuilt = np.asarray(Image.open(target).convert("RGB"))
    with Image.open(out_dir / "post_image.png") as current:
        existing = np.asarray(current.convert("RGB"))
    if rebuilt.shape != existing.shape or not np.array_equal(rebuilt, existing):
        return "final cover does not match a recomposition from the bound base, direction, and dossier"
    return None


def validate_art(out_dir: Path, dossier: dict, date: str, column: str, *,
                 history: list[dict] | None, recompute: bool = True) -> list[str]:
    """Full coded-art gate. history must be supplied explicitly (use load_history for production)."""
    errors: list[str] = []
    if history is None:
        return ["variety history was not checked; load committed branch history first"]
    names = ["artwork.py", "art_direction.json", "art_base.png", "post_image.png",
             "post_image.png.meta.json", "desk_dossier.json"]
    missing = [n for n in names if not (out_dir / n).is_file()]
    if missing:
        return [f"missing coded-art files: {', '.join(missing)}"]

    final = out_dir / "post_image.png"
    if final.stat().st_size > MAX_BYTES:
        errors.append("final image exceeds the 5 MB LinkedIn limit")
    try:
        with Image.open(final) as image:
            if image.format != "PNG" or image.size != (SIZE, SIZE):
                errors.append(f"final image must be a {SIZE} by {SIZE} PNG")
            pixels = np.asarray(image.convert("RGB"), dtype=float)
            final_fp = fingerprint(image)
    except Exception as exc:
        return [f"final image unreadable: {exc}"]
    if pixels.std() < 4:
        errors.append("final image appears blank")

    try:
        manifest = json.loads((out_dir / "art_direction.json").read_text(encoding="utf-8"))
        meta = json.loads((out_dir / "post_image.png.meta.json").read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"manifest or metadata is not valid JSON: {exc}"]

    if manifest.get("source") != "coded" or meta.get("source") != "coded":
        errors.append("new profile covers require coded provenance; ImageGen is legacy, historical only")
    for key in REQUIRED_META:
        if meta.get(key) in (None, "", []):
            errors.append(f"metadata missing {key}")
    if meta.get("date") != date:
        errors.append(f"metadata date {meta.get('date')!r} does not match {date!r}")
    if meta.get("kicker") != column:
        errors.append(f"metadata kicker {meta.get('kicker')!r} does not match {column!r}")
    errors.extend(validate_identity(manifest, meta, dossier))

    renderer_sha = sha256_file(out_dir / "artwork.py")
    dossier_sha = sha256_file(out_dir / "desk_dossier.json")
    base_sha = sha256_file(out_dir / "art_base.png")
    if meta.get("base_sha256") != base_sha:
        errors.append("stale provenance: metadata base hash does not match art_base.png")
    if meta.get("renderer_sha256") != renderer_sha or manifest.get("renderer", {}).get("sha256") != renderer_sha:
        errors.append("stale provenance: artwork.py changed after the cover was rendered")
    if meta.get("dossier_sha256") != dossier_sha or manifest.get("dossier_sha256") != dossier_sha:
        errors.append("stale provenance: dossier changed after the art was rendered")
    for key in ("style_family", "composition", "palette_key", "material", "silhouette", "light_model"):
        if meta.get(key) != manifest.get(key):
            errors.append(f"metadata {key} does not match the art direction manifest")
    if manifest.get("style_family") not in STYLE_FAMILIES:
        errors.append("style_family is outside the registered vocabulary (references/vocabulary.json)")
    if manifest.get("composition") not in COMPOSITIONS:
        errors.append("composition is outside the registered vocabulary")
    if manifest.get("material") not in MATERIALS:
        errors.append("material is outside the registered vocabulary")
    if manifest.get("light_model") not in LIGHT_MODELS:
        errors.append("light_model is outside the registered vocabulary")
    if not str(manifest.get("silhouette", "")).strip():
        errors.append("silhouette is required")
    palette = manifest.get("palette", [])
    if not (2 <= len(palette) <= 6) or not all(HEX.fullmatch(str(c)) for c in palette):
        errors.append("palette needs two to six #RRGGBB colors")
    if len(str(manifest.get("mechanism", "")).strip()) < 80:
        errors.append("mechanism must explain the decision in at least 80 characters")
    if manifest.get("renderer", {}).get("size") != [SIZE, SIZE]:
        errors.append("renderer must declare a 1080 by 1080 size")

    artwork_source = (out_dir / "artwork.py").read_text(encoding="utf-8")
    errors.extend(validate_anchors(manifest, dossier))
    errors.extend(validate_art_text(manifest, dossier, artwork_source))

    review = manifest.get("visual_review", {})
    if review.get("reviewed_post_image_sha256") != sha256_file(final):
        errors.append("visual review does not match the current final image hash")
    if review.get("reviewed_art_base_sha256") != base_sha:
        errors.append("visual review does not match the current art base hash")
    if review.get("full_size_checked") is not True or review.get("thumbnail_300_checked") is not True:
        errors.append("visual review must inspect the full-size cover and a 300 px thumbnail")
    checks = review.get("checks", {})
    for key in CHECK_KEYS:
        if checks.get(key) is not True:
            errors.append(f"visual review check not passed: {key}")

    if recompute and not errors:
        rebuilt = recompute_base(out_dir)
        if rebuilt is None:
            errors.append("artwork.py failed to re-render during recomputation")
        elif rebuilt != base_sha:
            errors.append("recomputed base hash differs from art_base.png; artwork.py does not reproduce it")
        if rebuilt is not None and not any(e.startswith("stale provenance") for e in errors):
            mismatch = recompose_matches(out_dir, manifest)
            if mismatch:
                errors.append(mismatch)

    candidate = {key: manifest.get(key) for key in DIMENSIONS}
    candidate.update(final_fp)
    run_iso = str(dossier.get("run_date", ""))
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", run_iso):
        return errors + ["dossier run_date must be an ISO date for the variety window"]
    previous_history, previous = select_history(history, run_iso)
    errors.extend(compare(candidate, previous_history, previous))
    return errors


# ----- attempt budget -------------------------------------------------------
def record_attempt(usage_path: Path, limit: int = ATTEMPT_LIMIT) -> int:
    """Count one artwork render attempt; raise once the budget is spent."""
    usage = json.loads(usage_path.read_text()) if usage_path.is_file() else {}
    attempts = int(usage.get("art_attempts", 0))
    if attempts >= limit:
        raise RuntimeError(f"art attempt budget of {limit} is spent; finish as needs-attention")
    usage["art_attempts"] = attempts + 1
    usage_path.parent.mkdir(parents=True, exist_ok=True)
    usage_path.write_text(json.dumps(usage, indent=2) + "\n")
    return attempts + 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default="out")
    parser.add_argument("--date", required=True, help="ISO run date")
    parser.add_argument("--column", default="TEXAS DESK")
    parser.add_argument("--repo", default=str(ROOT))
    parser.add_argument("--run-branch")
    args = parser.parse_args()
    out_dir = Path(args.out_dir).resolve()
    dossier = json.loads((out_dir / "desk_dossier.json").read_text(encoding="utf-8"))
    meta = json.loads((out_dir / "post_image.png.meta.json").read_text(encoding="utf-8"))
    try:
        history = load_history(Path(args.repo), args.date, args.run_branch)
    except HistoryError as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)], "history_compared": 0}, indent=2))
        return 1
    errors = validate_art(out_dir, dossier, meta.get("date", ""), args.column, history=history)
    print(json.dumps({"ok": not errors, "errors": errors, "history_compared": len(history)}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
