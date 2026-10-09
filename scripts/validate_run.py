#!/usr/bin/env python3
"""Validate a complete Texas Desk output package before it is committed."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

import yaml
from PIL import Image

from check_post import validate_post
from check_score import validate_score
from prose_rules import check_prose

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_GATES = {
    "named_subject", "recent_decision", "decision_owner", "texas_ai_consequence",
    "primary_source", "independent_corroboration", "position_or_accountability_read",
    "not_recent_repeat", "conflict_clear", "political_neutrality",
}


def is_web_url(value: object) -> bool:
    try:
        parsed = urlparse(str(value))
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def parse_date(value: object, label: str, errors: list[str]) -> dt.date | None:
    try:
        return dt.date.fromisoformat(str(value))
    except (TypeError, ValueError):
        errors.append(f"{label} must be an ISO date")
        return None


def validate_source(row: object, label: str, errors: list[str], *, independent: bool = False) -> None:
    if not isinstance(row, dict):
        errors.append(f"{label} must be an object")
        return
    for field in ("url", "title", "publisher"):
        if not row.get(field):
            errors.append(f"{label} missing {field}")
    if not is_web_url(row.get("url")):
        errors.append(f"{label} URL must be HTTP or HTTPS")
    if "published_at" in row:
        parse_date(row.get("published_at"), f"{label} published_at", errors)
    if independent and row.get("independent_of_subject") is not True:
        errors.append(f"{label} must be marked independent_of_subject true")


def require_file(path: Path, errors: list[str]) -> bool:
    if not path.is_file() or path.stat().st_size == 0:
        errors.append(f"missing or empty file: {path}")
        return False
    return True


def validate(out_dir: Path, history_root: str | None = None, run_branch: str | None = None) -> dict:
    errors: list[str] = []
    dossier_path = out_dir / "desk_dossier.json"
    if not require_file(dossier_path, errors):
        return {"ok": False, "errors": errors}
    try:
        dossier = json.loads(dossier_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"ok": False, "errors": [f"dossier JSON invalid: {exc}"]}

    if dossier.get("schema_version") != 1:
        errors.append("dossier schema_version must be 1")
    run_date = parse_date(dossier.get("run_date"), "dossier run_date", errors)
    state = yaml.safe_load((ROOT / "config/state.yaml").read_text(encoding="utf-8"))
    allowed_windows = {
        int(state["decision_window_days"]), int(state["broadening_window_days"])
    }
    if dossier.get("window_days") not in allowed_windows:
        errors.append(f"dossier window_days must be one of {sorted(allowed_windows)}")

    if dossier.get("no_target_this_cycle") is True:
        if dossier.get("window_days") != state["broadening_window_days"]:
            errors.append("no-target requires the completed broadening window")
        if dossier.get("selected_subject") or dossier.get("selected_decision"):
            errors.append("no-target dossier cannot include a selected subject or decision")
        if not dossier.get("_validation_note"):
            errors.append("no-target dossier lacks _validation_note")
        errors.extend(check_prose(str(dossier.get("_validation_note", ""))))
        dropped = dossier.get("dropped_candidates")
        if not isinstance(dropped, list) or not dropped:
            errors.append("no-target dossier needs a nonempty dropped_candidates list")
        else:
            for index, candidate in enumerate(dropped, start=1):
                label = f"dropped candidate {index}"
                if not isinstance(candidate, dict):
                    errors.append(f"{label} must be an object")
                    continue
                for field in ("subject", "decision", "drop_reason"):
                    if not candidate.get(field):
                        errors.append(f"{label} missing {field}")
                sources = candidate.get("sources")
                if not isinstance(sources, list) or not sources:
                    errors.append(f"{label} needs attempted source records")
                else:
                    for source_index, source in enumerate(sources, start=1):
                        validate_source(source, f"{label} source {source_index}", errors)
        return {"ok": not errors, "errors": errors, "mode": "no-target"}

    if dossier.get("no_target_this_cycle") is not False:
        errors.append("profile dossier must set no_target_this_cycle false")

    for key in ("selected_subject", "selected_decision", "analysis",
                "gate_results", "verified_facts"):
        if not dossier.get(key):
            errors.append(f"dossier missing {key}")

    subject = dossier.get("selected_subject") or {}
    for field in ("full_name", "role", "organization", "role_category", "texas_tie", "place_label"):
        if not subject.get(field):
            errors.append(f"selected_subject missing {field}")
    if len(str(subject.get("full_name", "")).split()) < 2:
        errors.append("selected_subject full_name must contain at least two words")
    if subject.get("role_category") not in {"founder", "operator", "public", "research"}:
        errors.append("selected_subject role_category is invalid")
    validate_source(subject.get("role_source"), "selected_subject role_source", errors)

    decision = dossier.get("selected_decision") or {}
    for field in (
        "what_happened", "decision_anchor", "date", "owner_evidence", "alternative_available",
        "ai_nexus", "texas_consequence", "next_check",
    ):
        if not decision.get(field):
            errors.append(f"selected_decision missing {field}")
    decision_date = parse_date(decision.get("date"), "selected_decision date", errors)
    if run_date and decision_date and dossier.get("window_days") in allowed_windows:
        age = (run_date - decision_date).days
        if age < 0:
            errors.append("selected decision is dated after the run date")
        elif age > int(dossier["window_days"]):
            errors.append("selected decision falls outside the dossier window")

    primary = decision.get("primary_source")
    validate_source(primary, "selected_decision primary_source", errors)
    corroborators = decision.get("corroborating_sources")
    if not isinstance(corroborators, list) or not corroborators:
        errors.append("selected_decision needs a corroborating source")
    else:
        for index, source in enumerate(corroborators, start=1):
            validate_source(source, f"selected_decision corroborating source {index}", errors)
        if not any(
            isinstance(source, dict) and source.get("independent_of_subject") is True
            for source in corroborators
        ):
            errors.append("selected_decision needs an independent corroborating source")
        source_urls = [str(row.get("url", "")) for row in corroborators if isinstance(row, dict)]
        if isinstance(primary, dict) and primary.get("url") in source_urls:
            errors.append("primary and corroborating source URLs must differ")

    analysis = dossier.get("analysis") or {}
    if decision.get("public_policy_or_electoral") is True:
        if analysis.get("editorial_mode") != "neutral_accountability":
            errors.append("public-policy dossier must use neutral_accountability")
        if analysis.get("assessment") != "not_applicable":
            errors.append("public-policy dossier assessment must be not_applicable")
    else:
        if analysis.get("editorial_mode") != "execution_assessment":
            errors.append("non-policy dossier must use execution_assessment")
        if analysis.get("assessment") not in {"sharp", "mixed", "weak"}:
            errors.append("non-policy dossier assessment must be sharp, mixed, or weak")
    if analysis.get("conflict_screen") != "clear":
        errors.append("analysis conflict_screen must be clear")
    for field in ("evidence_for", "evidence_against"):
        if not isinstance(analysis.get(field), list) or not analysis.get(field):
            errors.append(f"analysis {field} must be a nonempty list")
    for field in ("structural_read", "forward_implication"):
        if not analysis.get(field):
            errors.append(f"analysis missing {field}")

    gate_results = dossier.get("gate_results")
    if isinstance(gate_results, dict):
        missing_gates = REQUIRED_GATES - set(gate_results)
        if missing_gates:
            errors.append(f"dossier gates missing {', '.join(sorted(missing_gates))}")
        if not all(gate_results.get(name) is True for name in REQUIRED_GATES):
            errors.append("one or more required dossier gate results are not true")
    elif gate_results is not None:
        errors.append("gate_results must be an object")

    facts = dossier.get("verified_facts")
    if isinstance(facts, list):
        for index, fact in enumerate(facts, start=1):
            if not isinstance(fact, dict) or not fact.get("claim"):
                errors.append(f"verified fact {index} lacks a claim")
                continue
            urls = fact.get("source_urls")
            if not isinstance(urls, list) or not urls or not all(is_web_url(url) for url in urls):
                errors.append(f"verified fact {index} needs source_urls")
    elif facts is not None:
        errors.append("verified_facts must be a list")

    required_phrases = dossier.get("required_post_phrases")
    if not isinstance(required_phrases, list):
        errors.append("required_post_phrases must be a list")
    else:
        normalized = {str(value).casefold() for value in required_phrases}
        for value in (subject.get("full_name"), decision.get("decision_anchor")):
            if str(value).casefold() not in normalized:
                errors.append(f"required_post_phrases must include {value!r}")

    post_path = out_dir / "final_post.md"
    if require_file(post_path, errors):
        config = yaml.safe_load((ROOT / "config/brand.yaml").read_text(encoding="utf-8"))
        post_report = validate_post(post_path.read_text(encoding="utf-8"), dossier, config)
        errors.extend(f"post: {item}" for item in post_report["errors"])
    else:
        post_report = {"ok": False, "metrics": {}}

    score_path = out_dir / "score_report.json"
    if require_file(score_path, errors):
        try:
            score = json.loads(score_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"score JSON invalid: {exc}")
            score = {}
        rubric = yaml.safe_load((ROOT / "config/rubric.yaml").read_text(encoding="utf-8"))["rubric"]
        errors.extend(validate_score(score, rubric))
        for row in score.get("criteria", []):
            if isinstance(row, dict):
                errors.extend(check_prose(str(row.get("notes", ""))))

    artwork_dir = ROOT / ".agents/skills/texas-desk-artwork/scripts"
    if str(artwork_dir) not in sys.path:
        sys.path.insert(0, str(artwork_dir))
    import art_gate  # noqa: E402

    image_path = out_dir / "post_image.png"
    if require_file(image_path, errors):
        try:
            with Image.open(image_path) as image:
                if image.format != "PNG" or image.size != (1080, 1080):
                    errors.append(
                        f"image must be a 1080 by 1080 PNG, got {image.format} {image.size}"
                    )
        except Exception as exc:
            errors.append(f"image unreadable: {exc}")
    meta_path = Path(str(image_path) + ".meta.json")
    if require_file(meta_path, errors):
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"image metadata invalid: {exc}")
            meta = {}
        if meta.get("kicker") != "TEXAS DESK":
            errors.append("image metadata kicker must be TEXAS DESK")
        errors.extend(check_prose(str(meta.get("headline", ""))))
        history_repo = Path(history_root).resolve() if history_root else ROOT
        history = art_gate.load_history(history_repo, str(dossier.get("run_date", "")), run_branch)
        errors.extend(art_gate.validate_art(
            out_dir, dossier, str(meta.get("date", "")), "TEXAS DESK", history=history,
        ))
        report_history = len(history)
    else:
        report_history = 0

    return {
        "ok": not errors,
        "errors": errors,
        "mode": "profile",
        "history_compared": report_history,
        "post_metrics": post_report.get("metrics", {}),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="out")
    parser.add_argument("--report")
    parser.add_argument("--history-root", default=str(ROOT),
                        help="repository whose origin/codex/texas-desk-* branches supply variety history")
    parser.add_argument("--run-branch", help="this run's branch, excluded from its own history")
    args = parser.parse_args()
    result = validate(Path(args.out_dir), args.history_root, args.run_branch)
    rendered = json.dumps(result, indent=2, ensure_ascii=False)
    if args.report:
        Path(args.report).write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
