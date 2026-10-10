#!/usr/bin/env python3
"""Extract one Gmail tool result from a session JSONL transcript, without retyping it.

Selects the latest requested Gmail readback for this draft; a later failed or incomplete
read invalidates older evidence. The parsed response must carry the requested draft id.
Writes the parsed payload to --out (created with 0600 permissions) and prints only
a small summary (record index, tool name, payload keys, raw length).

Usage:
  python3 scripts/extract_gmail_tool_result.py TRANSCRIPT.jsonl DRAFT_ID OUT.json \
      [--tool get_draft] [--require-raw]
"""

import argparse
import json
import os
import sys


def _text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"]
        return "".join(parts)
    return ""


def extract(transcript, record_id, tool, require_raw):
    requests = {}
    found = None
    latest_request = None
    with open(transcript, encoding="utf-8") as fh:
        for index, line in enumerate(fh):
            if not line.strip():
                continue
            rec = json.loads(line)
            message = rec.get("message") or {}
            content = message.get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use":
                    name = block.get("name", "")
                    args = block.get("input") or {}
                    target = args.get("draftId", args.get("draft_id", args.get("id")))
                    matches = name.endswith(tool) and target == record_id
                    requests[block.get("id")] = (name, matches)
                    if matches:
                        found = None
                        latest_request = block.get("id")
                elif block.get("type") == "tool_result":
                    name, matches = requests.get(block.get("tool_use_id"), ("", False))
                    if not matches or block.get("tool_use_id") != latest_request or block.get("is_error"):
                        continue
                    try:
                        payload = json.loads(_text_of(block.get("content")))
                    except (TypeError, ValueError):
                        continue
                    if not isinstance(payload, dict) or payload.get("id") != record_id:
                        continue
                    if require_raw and "raw" not in payload:
                        continue
                    found = (index, name, payload)
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("transcript")
    parser.add_argument("draft_id")
    parser.add_argument("out")
    parser.add_argument("--tool", default="get_draft")
    parser.add_argument("--require-raw", action="store_true")
    args = parser.parse_args()

    found = extract(args.transcript, args.draft_id, args.tool, args.require_raw)
    if found is None:
        print("no matching tool result", file=sys.stderr)
        return 1
    index, name, payload = found
    fd = os.open(args.out, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(fd, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(payload, fh)
    print(json.dumps({
        "record_index": index,
        "tool": name,
        "keys": sorted(payload.keys()),
        "raw_chars": len(payload.get("raw", "")),
        "label_ids": payload.get("labelIds"),
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
