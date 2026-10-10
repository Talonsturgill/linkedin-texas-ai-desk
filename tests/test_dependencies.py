import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import art_smoke


class DependencyTests(unittest.TestCase):
    def test_matching_versions_do_not_install(self):
        pins = {"Pillow": "12.3.0", "numpy": "2.4.6", "PyYAML": "6.0.1"}
        with patch.object(art_smoke.importlib.metadata, "version", side_effect=pins.__getitem__), \
                patch.object(art_smoke.importlib.util, "find_spec", return_value=object()), \
                patch.object(art_smoke.subprocess, "run") as install:
            self.assertEqual(art_smoke.ensure_dependencies(), [])
            install.assert_not_called()

    def test_present_but_drifted_version_is_repaired(self):
        versions = ["12.3.0", "2.5.2", "6.0.1", "12.3.0", "2.4.6", "6.0.1"]
        with patch.object(art_smoke.importlib.metadata, "version", side_effect=versions), \
                patch.object(art_smoke.importlib.util, "find_spec", return_value=object()), \
                patch.object(art_smoke.subprocess, "run") as install:
            self.assertEqual(art_smoke.ensure_dependencies(), ["numpy"])
            install.assert_called_once()
            self.assertTrue(install.call_args.kwargs["check"])

    def test_failed_repair_cannot_report_available(self):
        with patch.object(art_smoke.importlib.metadata, "version", return_value="0.0.0"), \
                patch.object(art_smoke.importlib.util, "find_spec", return_value=object()), \
                patch.object(art_smoke.subprocess, "run"):
            with self.assertRaises(RuntimeError):
                art_smoke.ensure_dependencies()


if __name__ == "__main__":
    unittest.main()
