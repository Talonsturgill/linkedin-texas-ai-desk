"""Recompute the rubric instead of trusting a model's ship flag or total."""

from __future__ import annotations

import math


def numeric(value: object) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def validate_score(score: dict, rubric: dict) -> list[str]:
    errors: list[str] = []
    expected = {row["name"]: row["weight"] for row in rubric["criteria"]}
    rows = score.get("criteria")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        return ["score criteria must be a list of objects"]
    names = [row.get("name") for row in rows]
    if sorted(str(name) for name in names) != sorted(expected):
        errors.append("score criteria must match every rubric name exactly once")
    total = 0.0
    for row in rows:
        name, weight, value = row.get("name"), row.get("weight"), row.get("score")
        if not numeric(weight) or name not in expected or not math.isclose(
                weight, expected.get(name, -1), abs_tol=1e-9):
            errors.append(f"score weight differs from rubric: {name}")
        if not numeric(value) or not 0 <= value <= 10:
            errors.append(f"score must be a finite number from 0 through 10: {name}")
        elif name in expected:
            total += expected[name] * value
        if not isinstance(row.get("notes"), str) or not row["notes"].strip():
            errors.append(f"score lacks evidence note: {name}")
    reported = score.get("weighted_total")
    if not numeric(reported) or not math.isclose(reported, total, abs_tol=0.000001):
        errors.append("score weighted_total does not equal the recomputed rubric total")
    hard = score.get("hard_fail_checks")
    expected_hard = {row["name"] for row in rubric["hard_fail_checks"]}
    if not isinstance(hard, dict) or set(hard) != expected_hard or any(
            value is not True for value in (hard.values() if isinstance(hard, dict) else [])):
        errors.append("every configured hard-fail check must be recorded individually as true")
    if score.get("hard_failures") != []:
        errors.append("score hard_failures must be an empty list")
    if score.get("threshold") != rubric["ship_threshold"]:
        errors.append("score threshold differs from rubric")
    if score.get("ship") is not True or total < rubric["ship_threshold"]:
        errors.append("recomputed score is not shippable")
    return errors
