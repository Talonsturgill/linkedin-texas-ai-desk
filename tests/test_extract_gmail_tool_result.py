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
        self.assertIsNone(extractor.extract(FIXTURE, "draft-fixture-2", "list_drafts", True))
        self.assertIsNotNone(extractor.extract(FIXTURE, "draft-fixture-2", "list_drafts", False))

    def test_cli_writes_owner_only_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "raw.json"
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
