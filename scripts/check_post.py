#!/usr/bin/env python3
"""Deterministic hard gate for a Texas Desk LinkedIn post."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

import yaml
from prose_rules import check_prose

WORD_RE = re.compile(r"\b[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?\b")
NUMBER_RE = re.compile(r"(?<![A-Za-z])\$?\d[\d,]*(?:\.\d+)?")
LINK_RE = re.compile(r"(?:https?://|www\.)", re.I)
FIRST_PERSON_RE = re.compile(r"\b(?:I|me|my|mine|we|us|our|ours)\b", re.I)
POLITICAL_ADVOCACY_RE = re.compile(
    r"\b(?:vote\s+(?:for|against)|elect|re-elect|defeat|endorse|support\s+the\s+candidate|"
    r"oppose\s+the\s+candidate|best\s+candidate|worst\s+candidate)\b", re.I
)
EMOJI_RE = re.compile(
    "["
    "\U0001F1E6-\U0001F1FF"
    "\U0001F300-\U0001FAFF"
    "\U00002700-\U000027BF"
    "]+"
)
MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def ordinal(day: int) -> str:
    if 10 < day % 100 < 14:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return f"{day}{suffix}"


def display_date(iso_date: str) -> str:
    parsed = dt.date.fromisoformat(iso_date)
    return f"{MONTHS[parsed.month - 1]} {ordinal(parsed.day)}, {parsed.year}"


def split_post(text: str) -> tuple[str, list[str], str]:
    clean = text.strip()
    lines = clean.splitlines()
    while lines and not lines[-1].strip():
        lines.pop()
    tag_line = lines[-1].strip() if lines else ""
    tags = tag_line.split() if tag_line and all(
        token.startswith("#") for token in tag_line.split()
    ) else []
    body_lines = lines[:-1] if tags else lines
    body = "\n".join(body_lines).strip()
    return body, tags, tag_line


def canonical_number(token: str) -> str:
    value = token.replace("$", "").replace(",", "")
    if "." in value:
        value = value.rstrip("0").rstrip(".")
    value = value.lstrip("0") or "0"
    return value


def dossier_numbers(dossier: dict) -> set[str]:
    blob = json.dumps(dossier, ensure_ascii=False, sort_keys=True)
    return {canonical_number(match.group(0)) for match in NUMBER_RE.finditer(blob)}


def validate_post(post_text: str, dossier: dict, config: dict) -> dict:
    errors: list[str] = check_prose(post_text)
    body, tags, tag_line = split_post(post_text)
    platform = config["platform"]
    house = config["house_rules"]
    body_words = WORD_RE.findall(body)
    total_chars = len(post_text.strip())

    low, high = platform["body_words"]
    if not low <= len(body_words) <= high:
        errors.append(f"body word count {len(body_words)} outside {low} to {high}")
    if total_chars > platform["total_chars_max"]:
        errors.append(
            f"total character count {total_chars} exceeds {platform['total_chars_max']}"
        )

    for token in house["punctuation"]["forbidden"]:
        if token in body:
            errors.append(f"forbidden punctuation {token!r} appears in body")
    for token in ("“", "”", "‘", "’"):
        if token in body:
            errors.append("curly quotes are forbidden; use straight quotes")
            break
    if EMOJI_RE.search(body):
        errors.append("emoji appears in body")
    if FIRST_PERSON_RE.search(body):
        errors.append("first-person language appears in body")
    if POLITICAL_ADVOCACY_RE.search(body):
        errors.append("candidate or electoral advocacy appears in body")
    if LINK_RE.search(body):
        errors.append("post body contains a link; sources belong in the email")

    lowered = body.casefold()
    for phrase in config.get("banned_phrases", []):
        if phrase.casefold() in lowered:
            errors.append(f"banned phrase appears: {phrase}")

    expected_count = platform["hashtag_count"]
    if len(tags) != expected_count:
        errors.append(f"hashtag count {len(tags)} does not equal {expected_count}")
    whitelist = set(config["hashtags"]["whitelist"])
    for tag in tags:
        if tag not in whitelist:
            errors.append(f"hashtag is not approved: {tag}")
    if len(tags) != len(set(tags)):
        errors.append("hashtag line contains duplicates")

    nonempty_body_lines = [line.strip() for line in body.splitlines() if line.strip()]
    if not nonempty_body_lines or not nonempty_body_lines[-1].endswith("?"):
        errors.append("body must end with a specific engagement question")
    hook = " ".join(nonempty_body_lines[:2])
    if len(hook) > platform["hook_chars_max"]:
        errors.append(
            f"first two nonempty lines are {len(hook)} characters, above hook cap "
            f"{platform['hook_chars_max']}"
        )

    if dossier.get("no_target_this_cycle"):
        errors.append("a no-target dossier cannot have a final post")
    subject = dossier.get("selected_subject") or {}
    decision = dossier.get("selected_decision") or {}
    full_name = subject.get("full_name", "")
    organization = subject.get("organization", "")
    decision_anchor = decision.get("decision_anchor", "")
    for label, value in (("subject full name", full_name),
                         ("subject organization", organization),
                         ("decision anchor", decision_anchor)):
        if not value or value.casefold() not in lowered:
            errors.append(f"{label} is missing from body")
    for phrase in dossier.get("required_post_phrases", []):
        if str(phrase).casefold() not in lowered:
            errors.append(f"required dossier phrase missing: {phrase}")

    if full_name and full_name.split()[-1].casefold() not in hook.casefold():
        errors.append("hook does not name the subject")
    if decision_anchor and decision_anchor.casefold() not in hook.casefold():
        errors.append("hook does not name the decision anchor")

    try:
        human_date = display_date(decision.get("date", ""))
        if human_date.casefold() not in lowered:
            errors.append(f"decision date must appear as {human_date}")
    except (TypeError, ValueError):
        errors.append("dossier decision date is missing or invalid")

    primary = decision.get("primary_source") or {}
    corroborators = decision.get("corroborating_sources") or []
    if not str(primary.get("url", "")).startswith("http"):
        errors.append("dossier primary source URL is missing")
    if not any(row.get("independent_of_subject") is True for row in corroborators):
        errors.append("dossier lacks an independent corroborating source")
    if not dossier.get("gate_results") or not all(dossier["gate_results"].values()):
        errors.append("not every dossier gate result is true")

    quotes_allowed = {
        str(row.get("text", "")) for row in subject.get("verbatim_quotes", [])
    }
    for quoted in re.findall(r'"([^"\n]+)"', body):
        if quoted not in quotes_allowed:
            errors.append(f"quote is not verbatim in dossier: {quoted[:80]}")

    allowed_numbers = dossier_numbers(dossier)
    for match in NUMBER_RE.finditer(body):
        raw = match.group(0)
        if canonical_number(raw) not in allowed_numbers:
            errors.append(f"numeral is not grounded in dossier: {raw}")

    public_policy = decision.get("public_policy_or_electoral") is True
    analysis = dossier.get("analysis") or {}
    if public_policy:
        if analysis.get("editorial_mode") != "neutral_accountability":
            errors.append("public-policy decision must use neutral_accountability mode")
        if analysis.get("assessment") != "not_applicable":
            errors.append("public-policy decision cannot receive an editorial rating")
        if re.search(r"\b(?:sharp|mediocre|wrong|better policy|worse policy)\b", body, re.I):
            errors.append("public-policy post contains a directional editorial rating")

    return {
        "ok": not errors,
        "errors": errors,
        "metrics": {
            "body_words": len(body_words),
            "total_chars": total_chars,
            "hook_chars": len(hook),
            "hashtags": tags,
            "tag_line": tag_line,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--post", required=True)
    parser.add_argument("--dossier", required=True)
    parser.add_argument("--config", default="config/brand.yaml")
    parser.add_argument("--report")
    args = parser.parse_args()

    post = Path(args.post).read_text(encoding="utf-8")
    dossier = json.loads(Path(args.dossier).read_text(encoding="utf-8"))
    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    report = validate_post(post, dossier, config)
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    if args.report:
        Path(args.report).write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
