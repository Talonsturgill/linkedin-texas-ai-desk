import base64
import io
import sys
import tempfile
import unittest
from email.message import EmailMessage
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from gmail_delivery import make_preview, verify
from build_email import render_html


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        buffer = io.BytesIO()
        Image.new("RGB", (160, 160), "navy").save(buffer, "JPEG")
        self.preview = buffer.getvalue()
        self.body = '<style>p{color:red}</style><p>Complete copy &amp; evidence.</p><a href="https://example.org/image">Full image</a>'
        self.payload = {"to": "editor@example.org", "subject": "Texas Desk test",
                        "payload": {"body": {"content": self.body}}}

    def raw(self, *, body=None, image=None, recipient="editor@example.org", subject="Texas Desk test"):
        message = EmailMessage()
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content("Plain alternative")
        message.add_alternative(self.body if body is None else body, subtype="html")
        message.add_attachment(self.preview if image is None else image, maintype="image", subtype="jpeg",
                               filename="texas-desk-cover-preview.jpg")
        return {"message": {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}}

    def test_readback_allows_style_stripping_and_google_link_wrapper(self):
        body = '<p>Complete copy &amp; evidence.</p><a href="https://www.google.com/url?q=https%3A%2F%2Fexample.org%2Fimage">Full image</a>'
        self.assertTrue(verify(self.payload, self.raw(body=body), {"labels": ["DRAFT"]}, self.preview)["ok"])

    def test_corrupt_attachment_fails(self):
        result = verify(self.payload, self.raw(image=self.preview[:-1]), {"labels": ["DRAFT"]}, self.preview)
        self.assertFalse(result["ok"])
        self.assertIn("cover preview missing, duplicated, or byte-mismatched", result["errors"])

    def test_lost_copy_and_changed_link_fail(self):
        for body in ('<p>Truncated</p>', self.body.replace('example.org/image', 'example.org/different')):
            with self.subTest(body=body):
                self.assertFalse(verify(self.payload, self.raw(body=body), {"labels": ["DRAFT"]}, self.preview)["ok"])

    def test_wrong_recipient_subject_and_sent_label_fail(self):
        for raw, labels in ((self.raw(recipient="wrong@example.org"), ["DRAFT"]),
                            (self.raw(subject="Wrong"), ["DRAFT"]),
                            (self.raw(), ["DRAFT", "SENT"]), (self.raw(), [])):
            with self.subTest(labels=labels):
                result = verify(self.payload, raw, {"label_ids": labels}, self.preview)
                self.assertFalse(result["ok"])
                self.assertNotIn("@", str(result))

    def test_missing_or_ambiguous_label_evidence_fails(self):
        for metadata in ({}, {"labels": ["DRAFT"], "message": {"labels": ["DRAFT"]}}):
            self.assertFalse(verify(self.payload, self.raw(), metadata, self.preview)["ok"])

    def test_preview_is_bounded_and_requires_approved_size(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.png"
            target = Path(folder) / "preview.jpg"
            Image.new("RGB", (1080, 1080), "navy").save(source)
            result = make_preview(source, target)
            self.assertLessEqual(result["bytes"], 4096)
            with Image.open(target) as preview:
                self.assertEqual(preview.size, (160, 160))
            Image.new("RGB", (500, 500), "navy").save(source)
            with self.assertRaises(ValueError):
                make_preview(source, target)

    def test_attachment_body_keeps_full_resolution_download(self):
        body = render_html(post="A supported decision.", image_url="https://example.org/full.png",
                           dossier={}, score={}, date="October 9th, 2026", branch="test",
                           commit="a" * 40, editor_note="Preview attached.", attachment_preview=True)
        self.assertNotIn("<img", body)
        self.assertIn("160-pixel preview", body)
        self.assertIn('href="https://example.org/full.png"', body)


if __name__ == "__main__":
    unittest.main()
