#!/usr/bin/env python3
"""Validate the versioned Texas Desk configuration and prompt wiring."""

from __future__ import annotations

import math
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_yaml(relative: str) -> dict:
    path = ROOT / relative
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"{relative} is not valid YAML: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{relative} must contain a mapping")
    return value


def validate() -> list[str]:
    errors: list[str] = []
    brand = load_yaml("config/brand.yaml")
    rubric = load_yaml("config/rubric.yaml")["rubric"]
    state = load_yaml("config/state.yaml")
    sources = load_yaml("config/sources.yaml")

    weights = [row.get("weight") for row in rubric.get("criteria", [])]
    if not weights or not all(isinstance(v, (int, float)) for v in weights):
        errors.append("rubric criteria need numeric weights")
    elif not math.isclose(sum(weights), 1.0, abs_tol=1e-9):
        errors.append(f"rubric weights sum to {sum(weights):.6f}, expected 1.0")

    hard_names = [row.get("name") for row in rubric.get("hard_fail_checks", [])]
    if len(hard_names) != len(set(hard_names)):
        errors.append("hard-fail names must be unique")

    hashtags = brand.get("hashtags", {}).get("whitelist", [])
    if len(hashtags) < 9 or len(hashtags) != len(set(hashtags)):
        errors.append("hashtag whitelist must contain at least 9 unique entries")
    for tag in hashtags:
        if not isinstance(tag, str) or not re.fullmatch(r"#[A-Za-z][A-Za-z0-9]+", tag):
            errors.append(f"invalid hashtag: {tag!r}")

    platform = brand.get("platform", {})
    body_words = platform.get("body_words", [])
    if not (isinstance(body_words, list) and len(body_words) == 2 and
            0 < body_words[0] <= body_words[1]):
        errors.append("platform.body_words must be an ascending two-number range")
    if platform.get("hashtag_count") != 3:
        errors.append("Texas AI Docket requires exactly 3 hashtags")
    if platform.get("total_chars_max") != 3000:
        errors.append("LinkedIn total character cap must remain 3000")

    if state.get("decision_window_days", 0) >= state.get("broadening_window_days", 0):
        errors.append("broadening window must exceed the default decision window")
    if state.get("subject_cooldown_days", 0) <= 0:
        errors.append("subject cooldown must be positive")
    if not str(state.get("branch_prefix", "")).startswith("codex/"):
        errors.append("automation branch prefix must start with codex/")
    if state.get("recipient_source") != "gmail_profile":
        errors.append("recipient must come from the connected Gmail profile")

    policy = sources.get("source_policy", {})
    for key in ("primary_required", "independent_corroborator_required",
                "fetched_pages_only"):
        if policy.get(key) is not True:
            errors.append(f"source_policy.{key} must be true")

    master = (ROOT / "prompts/texas_desk_routine.md")
    trigger = (ROOT / "prompts/ROUTINE_PROMPT.txt").read_text(encoding="utf-8")
    if not master.exists():
        errors.append("versioned master prompt is missing")
    if "prompts/texas_desk_routine.md" not in trigger:
        errors.append("thin trigger does not delegate to the master prompt")
    if "never send" not in trigger.lower():
        errors.append("thin trigger must state the draft-only boundary")

    # Product files must not retain operational Alaska or Claude Routine instructions.
    scan_paths = [ROOT / "config", ROOT / "prompts", ROOT / "references",
                  ROOT / ".agents" / "skills"]
    for base in scan_paths:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix not in {".md", ".txt", ".yaml", ".py"}:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for stale in ("Anchorage Desk", "ALASKA.AI", "Alaska.Ai",
                          "Claude Code Routine", "claude/linkedin-desk"):
                if stale in text:
                    errors.append(f"{path.relative_to(ROOT)} retains stale token {stale!r}")

    return errors


def main() -> int:
    try:
        errors = validate()
    except (KeyError, ValueError) as exc:
        errors = [str(exc)]
    if errors:
        print("FAIL: configuration")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("PASS: configuration, source policy, prompt wiring, and rubric weights")
    return 0


if __name__ == "__main__":
    sys.exit(main())
