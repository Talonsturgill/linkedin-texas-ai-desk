import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import extract_gmail_tool_result as extractor  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "gmail_transcript_sample.jsonl"


class ExtractGmailToolResultTest(unittest.TestCase):
    def test_selects_matching_get_draft_result(self):
        index, name, payload = extractor.extract(FIXTURE, "draft-fixture-1", "get_draft", True)
        self.assertEqual(index, 2)
        self.assertEqual(name, "mcp__Gmail__get_draft")
        self.assertEqual(payload["labelIds"], ["DRAFT"])
        self.assertIn("Synthetic body.", payload["raw"])

    def test_wrong_id_or_tool_returns_none(self):
        self.assertIsNone(extractor.extract(FIXTURE, "missing-draft", "get_draft", False))
        self.assertIsNone(extractor.extract(FIXTURE, "draft-fixture-2", "get_draft", False))

    def test_require_raw_skips_results_without_raw(self):
        records = [json.loads(line) for line in FIXTURE.read_text().splitlines()]
        records[2]["message"]["content"][0]["content"] = json.dumps({"id": "draft-fixture-1", "labelIds": ["DRAFT"]})
        with tempfile.TemporaryDirectory() as tmp:
            transcript = Path(tmp) / "metadata.jsonl"
            transcript.write_text("\n".join(map(json.dumps, records)))
            self.assertIsNone(extractor.extract(transcript, "draft-fixture-1", "get_draft", True))
            self.assertIsNotNone(extractor.extract(transcript, "draft-fixture-1", "get_draft", False))

    def test_later_failed_or_pending_read_invalidates_old_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            transcript = Path(tmp) / "session.jsonl"
            latest = {"message": {"content": [{"type": "tool_use", "id": "latest",
                       "name": "mcp__Gmail__get_draft", "input": {"draftId": "draft-fixture-1"}}]}}
            transcript.write_text(FIXTURE.read_text() + json.dumps(latest) + "\n")
            self.assertIsNone(extractor.extract(transcript, "draft-fixture-1", "get_draft", True))
            with transcript.open("a") as handle:
                handle.write(json.dumps({"message": {"content": [{"type": "tool_result",
                    "tool_use_id": "latest", "is_error": True, "content": "read failed"}]}}) + "\n")
            self.assertIsNone(extractor.extract(transcript, "draft-fixture-1", "get_draft", True))

    def test_cli_writes_owner_only_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "raw.json"
            out.write_text("old private result")
            out.chmod(0o644)
            argv = sys.argv
            try:
                sys.argv = ["extract", str(FIXTURE), "draft-fixture-1", str(out), "--require-raw"]
                self.assertEqual(extractor.main(), 0)
            finally:
                sys.argv = argv
            self.assertEqual(json.loads(out.read_text())["id"], "draft-fixture-1")
            self.assertEqual(out.stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
