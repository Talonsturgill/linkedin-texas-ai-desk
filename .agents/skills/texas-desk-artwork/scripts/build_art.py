#!/usr/bin/env python3
"""One deterministic build for a story's coded art: render, hash, direction, compose, thumbnail.

Author only artwork.py and art_direction.json (identity, vocabulary, mechanism, anchors, art_text).
Run this command, inspect out/post_image.png and out/thumb_300.png, record your real review in
visual_review, then run art_gate.py. This command never marks a visual check true. If the base or
final pixels change, any previous visual review is reset to pending.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import art_gate as gate  # noqa: E402
import compose_cover  # noqa: E402
from art_gate import ATTEMPT_LIMIT, CHECK_KEYS, record_attempt  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = Path(__file__).resolve().parents[4]


def pending_review() -> dict:
    return {
        "reviewed_post_image_sha256": None,
        "reviewed_art_base_sha256": None,
        "full_size_checked": False,
        "thumbnail_300_checked": False,
        "checks": {key: False for key in CHECK_KEYS},
        "findings": "pending: inspect out/post_image.png and out/thumb_300.png, then record the real review",
    }


def build(story: Path, usage: Path, limit: int = ATTEMPT_LIMIT) -> dict:
    attempt = record_attempt(usage, limit)
    try:
        result = subprocess.run([sys.executable, "-I", "artwork.py", "--out", "art_base.png"],
                                cwd=story, capture_output=True, text=True, timeout=240)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"artwork.py exceeded 240 seconds on attempt {attempt}") from exc
    if result.returncode != 0 or not (story / "art_base.png").is_file():
        raise RuntimeError(f"artwork.py failed on attempt {attempt}: {result.stderr[-300:]}")
    base_sha = gate.sha256_file(story / "art_base.png")

    direction_path = story / "art_direction.json"
    manifest = json.loads(direction_path.read_text(encoding="utf-8"))
    previous_review = manifest.get("visual_review", {})
    manifest["renderer"]["sha256"] = gate.sha256_file(story / "artwork.py")
    manifest["dossier_sha256"] = gate.sha256_file(story / "desk_dossier.json")
    manifest["visual_review"] = previous_review or pending_review()
    direction_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    compose_cover.compose(
        base_path=story / "art_base.png", headline=manifest["headline"], role=manifest["role"],
        date=manifest["date"], place=manifest["place"], coords=manifest.get("coordinates", ""),
        source="coded", out_path=story / "post_image.png", art_direction=direction_path,
        renderer=story / "artwork.py", dossier=story / "desk_dossier.json",
    )
    final_sha = gate.sha256_file(story / "post_image.png")
    with Image.open(story / "post_image.png") as image:
        image.convert("RGB").resize((300, 300), Image.Resampling.LANCZOS).save(story / "thumb_300.png", "PNG")

    review = manifest["visual_review"]
    pixels_changed = (review.get("reviewed_art_base_sha256") != base_sha
                      or review.get("reviewed_post_image_sha256") != final_sha)
    if pixels_changed:
        manifest["visual_review"] = pending_review()
    direction_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"attempt": attempt, "limit": limit, "base_sha256": base_sha, "post_image_sha256": final_sha,
            "review_reset": pixels_changed, "review_state": "pending" if pixels_changed else "kept_for_current_pixels"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--story-dir", required=True)
    parser.add_argument("--usage", default=str(ROOT / ".local/usage.json"))
    parser.add_argument("--limit", type=int, default=ATTEMPT_LIMIT)
    args = parser.parse_args()
    try:
        summary = build(Path(args.story_dir).resolve(), Path(args.usage).resolve(), args.limit)
    except RuntimeError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 3
    print(json.dumps({"ok": True, **summary}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
