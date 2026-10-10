#!/usr/bin/env python3
"""Build a bounded cover preview and verify Gmail's stored MIME without printing account data."""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import re
from email import policy
from email.parser import BytesParser
from email.utils import getaddresses
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from PIL import Image


class VisibleHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden = 0
        self.text = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag in {"style", "script", "head"}:
            self.hidden += 1
        if tag == "a":
            self.links.extend(value for key, value in attrs if key == "href" and value)

    def handle_endtag(self, tag):
        if tag in {"style", "script", "head"}:
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden:
            self.text.append(data)


def visible(html):
    parser = VisibleHTML()
    parser.feed(html)
    return " ".join(" ".join(parser.text).split()), parser.links


def canonical_link(url):
    parsed = urlparse(url)
    if parsed.hostname in {"google.com", "www.google.com"} and parsed.path == "/url":
        query = parse_qs(parsed.query)
        target = (query.get("q") or query.get("url") or [url])[0]
        if urlparse(target).scheme in {"https", "http"}:
            return target
    return url


def make_preview(source: Path, target: Path):
    with Image.open(source) as image:
        if image.size != (1080, 1080) or image.format != "PNG":
            raise ValueError("preview source must be the approved 1080-square PNG")
        image = image.convert("RGB").resize((160, 160), Image.Resampling.LANCZOS)
        for quality in (25, 20):
            buffer = io.BytesIO()
            image.save(buffer, "JPEG", quality=quality, optimize=True)
            data = buffer.getvalue()
            if len(data) <= 4096:
                break
        else:
            raise ValueError("preview exceeds the 4 KiB connector budget")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "size": [160, 160], "quality": quality}


def collect(value, keys):
    found = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key in keys:
                found.append(item)
            else:
                found.extend(collect(item, keys))
    elif isinstance(value, list):
        for item in value:
            found.extend(collect(item, keys))
    return found


def decode_raw(value):
    if isinstance(value, dict):
        rows = collect(value, {"raw"})
        if len(rows) != 1 or not isinstance(rows[0], str):
            raise ValueError("RAW response must contain exactly one raw MIME field")
        value = rows[0]
    if isinstance(value, str):
        value = value.encode("ascii")
    compact = re.sub(rb"\s", b"", value)
    return base64.b64decode(compact + b"=" * (-len(compact) % 4), altchars=b"-_", validate=True)


def verify(payload: dict, raw, metadata: dict, preview: bytes):
    errors = []
    message = BytesParser(policy=policy.default).parsebytes(decode_raw(raw))
    if str(message.get("Subject", "")) != payload["subject"]:
        errors.append("subject mismatch")
    recipients = [address.casefold() for _, address in getaddresses(message.get_all("To", []))]
    if recipients != [payload["to"].casefold()] or message.get("Cc") or message.get("Bcc"):
        errors.append("recipient mismatch or unexpected copy recipients")
    label_rows = collect(metadata, {"labelIds", "label_ids", "labels"})
    if len(label_rows) != 1 or not isinstance(label_rows[0], list):
        errors.append("readback must supply one actual label list")
    elif "DRAFT" not in label_rows[0] or "SENT" in label_rows[0]:
        errors.append("draft-only labels not verified")
    html_parts = [part for part in message.walk() if part.get_content_type() == "text/html"]
    if len(html_parts) != 1:
        errors.append("stored MIME needs exactly one HTML body")
    else:
        expected_html = payload["payload"]["body"]["content"]
        expected_text, expected_links = visible(expected_html)
        actual_text, actual_links = visible(html_parts[0].get_content())
        if expected_text != actual_text:
            errors.append("stored visible body differs from generated payload")
        if not set(map(canonical_link, expected_links)) <= set(map(canonical_link, actual_links)):
            errors.append("stored body is missing or changing a required link")
    attachments = [part for part in message.walk()
                   if part.get_filename() == "texas-desk-cover-preview.jpg"
                   and part.get_content_type() == "image/jpeg"]
    if len(attachments) != 1 or attachments[0].get_payload(decode=True) != preview:
        errors.append("cover preview missing, duplicated, or byte-mismatched")
    with Image.open(io.BytesIO(preview)) as image:
        if image.format != "JPEG" or image.size != (160, 160):
            errors.append("expected preview must be a 160-square JPEG")
    return {"ok": not errors, "errors": errors, "preview_sha256": hashlib.sha256(preview).hexdigest(),
            "body_comparison": "visible text and canonical link targets; not raw HTML byte equality",
            "draft_only": not errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    create = sub.add_parser("preview")
    create.add_argument("--image", required=True)
    create.add_argument("--out", required=True)
    check = sub.add_parser("verify")
    for name in ("payload", "raw", "metadata", "preview", "report"):
        check.add_argument("--" + name, required=True)
    args = parser.parse_args()
    try:
        if args.action == "preview":
            result = make_preview(Path(args.image), Path(args.out))
        else:
            raw_text = Path(args.raw).read_text()
            raw = json.loads(raw_text) if raw_text.lstrip().startswith("{") else raw_text.strip()
            result = verify(json.loads(Path(args.payload).read_text()), raw,
                            json.loads(Path(args.metadata).read_text()), Path(args.preview).read_bytes())
            Path(args.report).write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result))
        return 0 if result.get("ok", True) else 1
    except Exception:
        # Connector bodies and headers are private; never print exception values from them.
        print(json.dumps({"ok": False, "errors": ["invalid input or unreadable delivery evidence"]}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
