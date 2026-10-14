#!/usr/bin/env python3
"""Resolve the connected account from trusted connector metadata before any write."""

import argparse
import json
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
ADDRESS = re.compile(r"[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+")


def resolve_account(evidence: dict) -> dict:
    addresses = set()
    methods = []
    profile = evidence.get("profile", {})
    email = profile.get("emailAddress") if isinstance(profile, dict) else None
    if email and ADDRESS.fullmatch(str(email)):
        addresses.add(email.casefold())
        methods.append("connected_profile")
    for url in evidence.get("connector_view_urls", []):
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname != "mail.google.com":
            continue
        for email in parse_qs(parsed.query).get("authuser", []):
            if ADDRESS.fullmatch(email):
                addresses.add(email.casefold())
                methods.append("connector_authuser_metadata")
    if len(addresses) != 1:
        raise ValueError("connected account metadata is missing or conflicting; do not create a draft")
    return {"email": addresses.pop(), "verified": True, "evidence": sorted(set(methods))}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--out", default=".local/gmail_account.json")
    args = parser.parse_args()
    paths = [Path(args.evidence).resolve(), Path(args.out).resolve()]
    if any(not path.is_relative_to(ROOT / ".local") for path in paths):
        parser.error("account evidence and receipt must stay under ignored .local/")
    try:
        result = resolve_account(json.loads(paths[0].read_text()))
    except ValueError as exc:
        print(str(exc))
        return 2
    paths[1].parent.mkdir(parents=True, exist_ok=True)
    paths[1].write_text(json.dumps(result) + "\n")
    print(json.dumps({"verified": True, "evidence": result["evidence"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
