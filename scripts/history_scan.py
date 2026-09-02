#!/usr/bin/env python3
"""Build the subject cooldown and permanent decision blocklist from run branches."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

BRANCH_RE = re.compile(r"(?:origin/)?codex/texas-desk-(\d{4}-\d{2}-\d{2})(?:-\d+)?$")


def normalize(value: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value.casefold()).split())


def summarize(records: list[tuple[str, dict]], today: dt.date,
              cooldown_days: int) -> dict:
    recent_subjects: list[dict] = []
    covered_pairs: list[dict] = []
    seen_pairs: set[tuple[str, str]] = set()

    for branch, dossier in records:
        match = BRANCH_RE.search(branch)
        if not match or dossier.get("no_target_this_cycle"):
            continue
        run_date = dt.date.fromisoformat(match.group(1))
        subject = dossier.get("selected_subject") or {}
        decision = dossier.get("selected_decision") or {}
        name = str(subject.get("full_name", "")).strip()
        what = str(decision.get("what_happened", "")).strip()
        when = str(decision.get("date", "")).strip()
        if not name or not what:
            continue
        pair_key = (normalize(name), normalize(f"{what} {when}"))
        if pair_key not in seen_pairs:
            seen_pairs.add(pair_key)
            covered_pairs.append({
                "subject": name,
                "decision": what,
                "decision_date": when,
                "branch": branch,
            })
        age = (today - run_date).days
        if 0 <= age < cooldown_days:
            recent_subjects.append({
                "subject": name,
                "role_category": subject.get("role_category"),
                "profile_date": run_date.isoformat(),
                "eligible_after": (run_date + dt.timedelta(days=cooldown_days)).isoformat(),
                "branch": branch,
            })

    recent_subjects.sort(key=lambda row: row["profile_date"], reverse=True)
    covered_pairs.sort(key=lambda row: (row["subject"].casefold(), row["decision_date"]))
    return {
        "schema_version": 1,
        "as_of": today.isoformat(),
        "cooldown_days": cooldown_days,
        "recent_subjects": recent_subjects,
        "covered_subject_decision_pairs": covered_pairs,
        "branches_with_profiles": len(records),
    }


def git_output(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout


def read_records(repo: Path) -> list[tuple[str, dict]]:
    raw = git_output(
        repo, "for-each-ref", "--format=%(refname:short)",
        "refs/remotes/origin/codex/texas-desk-*",
    )
    records: list[tuple[str, dict]] = []
    for branch in sorted(filter(None, (line.strip() for line in raw.splitlines()))):
        shown = subprocess.run(
            ["git", "-C", str(repo), "show", f"{branch}:out/desk_dossier.json"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        if shown.returncode:
            continue
        try:
            records.append((branch, json.loads(shown.stdout)))
        except json.JSONDecodeError:
            continue
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--date", required=True, help="America/Chicago date in YYYY-MM-DD")
    parser.add_argument("--cooldown-days", type=int, default=21)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    today = dt.date.fromisoformat(args.date)
    records = read_records(Path(args.repo).resolve())
    result = summarize(records, today, args.cooldown_days)
    Path(args.out).write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        f"history: {len(result['recent_subjects'])} subjects cooling down, "
        f"{len(result['covered_subject_decision_pairs'])} permanent pairs"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
