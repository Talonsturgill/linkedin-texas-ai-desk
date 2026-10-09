"""Regression tests for the coded Texas Desk artwork gate, variety engine, and bootstrap."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/skills/texas-desk-artwork/scripts"
sys.path.insert(0, str(SCRIPTS))

import os  # noqa: E402
os.environ.setdefault("TEXAS_DESK_KIT", str(SCRIPTS))
import art_gate as gate  # noqa: E402
import art_kit  # noqa: E402
from PIL import Image, ImageOps  # noqa: E402

EX = ROOT / "examples/coded_art"
STORIES = ["fermi_tensorwave_2026-10-07", "sloan_dean_2026-09-30", "ben_johnson_2026-09-23"]


def story_entry(name: str, ref: str | None = None) -> dict:
    base = EX / name
    dossier = json.loads((base / "desk_dossier.json").read_text())
    return gate._entry(
        ref=ref or f"example:{name}", date=dossier["run_date"],
        png=(base / "post_image.png").read_bytes(),
        meta=json.loads((base / "post_image.png.meta.json").read_text()),
        manifest=json.loads((base / "art_direction.json").read_text()),
    )


def copy_story(name: str, target: Path) -> Path:
    destination = target / name
    shutil.copytree(EX / name, destination)
    return destination


def gate_errors(folder: Path, history: list[dict]) -> list[str]:
    dossier = json.loads((folder / "desk_dossier.json").read_text())
    meta = json.loads((folder / "post_image.png.meta.json").read_text())
    return gate.validate_art(folder, dossier, meta["date"], "TEXAS DESK", history=history)


class KitTests(unittest.TestCase):
    def test_smoke_render_has_expected_size_and_is_not_blank(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "smoke.png"
            self.assertEqual(art_kit.smoke_render(output), (128, 128))
            with Image.open(output) as image:
                self.assertEqual(image.size, (128, 128))
                self.assertGreater(len(set(image.convert("RGB").getdata())), 100)

    def test_clean_bootstrap_copy_renders_without_local_state(self) -> None:
        """A fresh checkout has no .local, out, or fonts; the smoke check must still pass."""
        with tempfile.TemporaryDirectory() as temporary:
            clone = Path(temporary) / "repo"
            shutil.copytree(
                ROOT, clone,
                ignore=shutil.ignore_patterns(".local", "out", "fonts", "__pycache__", ".git", "examples"),
            )
            result = subprocess.run(
                [sys.executable, str(clone / "scripts/art_smoke.py")],
                cwd=clone, capture_output=True, text=True, timeout=600,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads(result.stdout.strip().splitlines()[-1])
            self.assertEqual(report["coded_art"], "available")
            self.assertEqual(report["size"], [128, 128])


class GateTests(unittest.TestCase):
    def test_historical_examples_pass_full_gate_against_each_other(self) -> None:
        for name in STORIES:
            with self.subTest(story=name):
                history = [story_entry(other) for other in STORIES if other != name]
                self.assertEqual(gate_errors(EX / name, history), [])

    def test_relabeled_and_recolored_pixels_are_caught(self) -> None:
        """Same structure with new metadata and a recolored palette must still be refused."""
        with tempfile.TemporaryDirectory() as temporary:
            original = story_entry(STORIES[0], ref="branch:original")
            recolored = ImageOps.colorize(
                Image.open(EX / STORIES[0] / "post_image.png").convert("L"),
                black="#101820", white="#F0E0C0",
            )
            buffer = Path(temporary) / "recolored.png"
            recolored.save(buffer)
            fingerprint = gate.fingerprint(Image.open(buffer))
            self.assertLessEqual(gate.dhash_distance(original["dhash"], fingerprint["dhash"]), gate.DHASH_NEAR)
            self.assertGreaterEqual(gate.edge_similarity(original["edge"], fingerprint["edge"]), gate.EDGE_NEAR)

    def test_unrelated_covers_are_not_flagged(self) -> None:
        a, b = story_entry(STORIES[0]), story_entry(STORIES[1])
        self.assertGreater(gate.dhash_distance(a["dhash"], b["dhash"]), gate.DHASH_NEAR)
        self.assertLess(gate.edge_similarity(a["edge"], b["edge"]), gate.EDGE_NEAR)

    def test_repeated_style_family_or_composition_is_refused(self) -> None:
        candidate = story_entry(STORIES[0])
        clash = dict(story_entry(STORIES[1], ref="branch:clash"))
        clash["style_family"] = candidate["style_family"]
        errors = gate.compare(candidate, [clash], previous=None)
        self.assertTrue(any("style family repeats" in e for e in errors), errors)
        clash["style_family"] = "other"
        clash["composition"] = candidate["composition"]
        errors = gate.compare(candidate, [clash], previous=None)
        self.assertTrue(any("composition repeats" in e for e in errors), errors)

    def test_three_changed_dimensions_are_required_against_previous_cover(self) -> None:
        candidate = story_entry(STORIES[0])
        previous = dict(story_entry(STORIES[1], ref="branch:previous"))
        previous.update({key: candidate[key] for key in ("style_family", "composition", "palette_key", "material")})
        previous["silhouette"] = "other"
        errors = gate.compare(candidate, [], previous=previous)
        self.assertTrue(any("only 2 dimensions differ" in e for e in errors), errors)

    def test_stale_provenance_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            folder = copy_story(STORIES[1], Path(temporary))
            history = [story_entry(STORIES[0]), story_entry(STORIES[2])]
            (folder / "artwork.py").write_text((folder / "artwork.py").read_text() + "\n# edited later\n")
            errors = gate_errors(folder, history)
            self.assertTrue(any("artwork.py changed" in e for e in errors), errors)

    def test_dossier_change_after_render_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            folder = copy_story(STORIES[1], Path(temporary))
            dossier = json.loads((folder / "desk_dossier.json").read_text())
            dossier["selected_decision"]["next_check"] = "edited after rendering"
            (folder / "desk_dossier.json").write_text(json.dumps(dossier))
            errors = gate_errors(folder, [story_entry(STORIES[0])])
            self.assertTrue(any("dossier changed" in e for e in errors), errors)

    def test_visual_review_must_match_current_image(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            folder = copy_story(STORIES[2], Path(temporary))
            manifest = json.loads((folder / "art_direction.json").read_text())
            manifest["visual_review"]["reviewed_post_image_sha256"] = "0" * 64
            (folder / "art_direction.json").write_text(json.dumps(manifest))
            errors = gate_errors(folder, [])
            self.assertTrue(any("visual review does not match" in e for e in errors), errors)

    def test_visual_review_requires_every_acceptance_check(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            folder = copy_story(STORIES[2], Path(temporary))
            manifest = json.loads((folder / "art_direction.json").read_text())
            manifest["visual_review"]["checks"]["distinctive_material_object"] = False
            (folder / "art_direction.json").write_text(json.dumps(manifest))
            errors = gate_errors(folder, [])
            self.assertIn("visual review check not passed: distinctive_material_object", errors)

    def test_anchor_must_bind_to_verbatim_dossier_claim(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            folder = copy_story(STORIES[0], Path(temporary))
            manifest = json.loads((folder / "art_direction.json").read_text())
            manifest["visual_anchors"][0]["claim"] = "A paraphrased claim that the dossier never states."
            (folder / "art_direction.json").write_text(json.dumps(manifest))
            errors = gate_errors(folder, [])
            self.assertTrue(any("not verbatim" in e for e in errors), errors)

    def test_art_text_must_come_from_dossier(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            folder = copy_story(STORIES[0], Path(temporary))
            manifest = json.loads((folder / "art_direction.json").read_text())
            manifest["art_text"][0]["source_phrase"] = "December 31st"
            (folder / "art_direction.json").write_text(json.dumps(manifest))
            errors = gate_errors(folder, [])
            self.assertTrue(any("source phrase is not verbatim" in e for e in errors), errors)

    def test_legacy_imagegen_is_rejected_for_new_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            folder = copy_story(STORIES[1], Path(temporary))
            meta = json.loads((folder / "post_image.png.meta.json").read_text())
            meta["source"] = "imagegen"
            (folder / "post_image.png.meta.json").write_text(json.dumps(meta))
            errors = gate_errors(folder, [])
            self.assertTrue(any("require coded provenance" in e for e in errors), errors)

    def test_attempt_budget_refuses_a_third_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            usage = Path(temporary) / "usage.json"
            self.assertEqual(gate.record_attempt(usage, 2), 1)
            self.assertEqual(gate.record_attempt(usage, 2), 2)
            with self.assertRaises(RuntimeError):
                gate.record_attempt(usage, 2)
            self.assertEqual(json.loads(usage.read_text())["art_attempts"], 2)

    def test_render_art_budget_is_recorded_and_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            usage = Path(temporary) / "usage.json"
            output = Path(temporary) / "base.png"
            command = [sys.executable, str(SCRIPTS / "render_art.py"), "--workdir", str(EX / STORIES[1]),
                       "--out", str(output), "--usage", str(usage), "--limit", "1"]
            first = subprocess.run(command, capture_output=True, text=True, timeout=300)
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            second = subprocess.run(command, capture_output=True, text=True, timeout=300)
            self.assertEqual(second.returncode, 3)


class HistoryTests(unittest.TestCase):
    def test_cross_branch_history_is_read_from_committed_refs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary) / "repo"
            repo.mkdir()
            env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
                   "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com", "PATH": "/usr/bin:/bin"}

            def git(*args: str) -> None:
                subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, env=env)

            git("init", "-q", "-b", "main")
            (repo / "README").write_text("seed\n")
            git("add", "README")
            git("commit", "-q", "-m", "seed")
            for branch, name in [("codex/texas-desk-2026-09-23", STORIES[2]), ("codex/texas-desk-2026-10-07", STORIES[0])]:
                git("checkout", "-q", "-B", branch, "main")
                (repo / "out").mkdir(exist_ok=True)
                for filename in ("post_image.png", "post_image.png.meta.json", "art_direction.json"):
                    shutil.copy(EX / name / filename, repo / "out" / filename)
                git("add", "-f", "out")
                git("commit", "-q", "-m", branch)
                git("update-ref", f"refs/remotes/origin/{branch}", "HEAD")
            git("checkout", "-q", "main")

            history = gate.load_history(repo, "2026-10-09")
            self.assertEqual([entry["date"] for entry in history], ["2026-09-23", "2026-10-07"])
            self.assertEqual(gate.load_history(repo, "2026-10-07")[0]["date"], "2026-09-23")
            self.assertEqual(len(gate.load_history(repo, "2026-10-09", "codex/texas-desk-2026-10-07")), 1)

            window, previous = gate.select_history(history, "2026-10-09")
            self.assertEqual(previous["date"], "2026-10-07")
            self.assertEqual(len(window), 2)

    def test_candidate_matching_a_historic_branch_cover_is_refused(self) -> None:
        historic = story_entry(STORIES[2], ref="origin/codex/texas-desk-2026-09-23")
        candidate = story_entry(STORIES[2], ref="candidate")
        errors = gate.compare(candidate, [historic], previous=None)
        self.assertTrue(any("near-identical" in e or "matches" in e for e in errors), errors)


class ReviewRegressionTests(unittest.TestCase):
    def test_tampered_final_with_recomputed_review_hash_fails(self) -> None:
        """A different final PNG with an updated review hash must still fail the recomposition check."""
        with tempfile.TemporaryDirectory() as temporary:
            folder = copy_story(STORIES[1], Path(temporary))
            shutil.copy(EX / STORIES[0] / "post_image.png", folder / "post_image.png")
            manifest = json.loads((folder / "art_direction.json").read_text())
            manifest["visual_review"]["reviewed_post_image_sha256"] = gate.sha256_file(folder / "post_image.png")
            (folder / "art_direction.json").write_text(json.dumps(manifest))
            meta = json.loads((folder / "post_image.png.meta.json").read_text())
            errors = gate_errors(folder, [story_entry(STORIES[0])])
            self.assertIn(
                "final cover does not match a recomposition from the bound base, direction, and dossier", errors)

    def test_manifest_and_metadata_must_agree_on_headline(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            folder = copy_story(STORIES[2], Path(temporary))
            manifest = json.loads((folder / "art_direction.json").read_text())
            manifest["headline"] = "A different headline"
            (folder / "art_direction.json").write_text(json.dumps(manifest))
            errors = gate_errors(folder, [])
            self.assertIn("manifest and metadata disagree on headline", errors)

    def test_place_and_decision_anchor_must_match_dossier(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            folder = copy_story(STORIES[2], Path(temporary))
            dossier = json.loads((folder / "desk_dossier.json").read_text())
            dossier["selected_subject"]["place_label"] = "HOUSTON"
            (folder / "desk_dossier.json").write_text(json.dumps(dossier))
            errors = gate_errors(folder, [])
            self.assertTrue(any("place does not match" in e for e in errors), errors)

    def test_art_label_must_be_the_supported_abbreviation_and_drawn(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            folder = copy_story(STORIES[0], Path(temporary))
            manifest = json.loads((folder / "art_direction.json").read_text())
            manifest["art_text"][1]["text"] = "OCT 99"
            (folder / "art_direction.json").write_text(json.dumps(manifest))
            errors = gate_errors(folder, [])
            self.assertTrue(any("not the supported label" in e for e in errors), errors)
            self.assertTrue(any("not drawn by artwork.py" in e for e in errors), errors)

    def test_display_date_uses_publication_ordinals(self) -> None:
        self.assertEqual(gate.display_date("2026-10-07"), "OCTOBER 7TH, 2026")
        self.assertEqual(gate.display_date("2026-09-22"), "SEPTEMBER 22ND, 2026")
        self.assertEqual(gate.display_date("2026-09-23"), "SEPTEMBER 23RD, 2026")
        self.assertEqual(gate.display_date("2026-09-11"), "SEPTEMBER 11TH, 2026")
        self.assertEqual(gate.expected_label("September 30th"), "SEP 30")

    def test_unregistered_vocabulary_name_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            folder = copy_story(STORIES[1], Path(temporary))
            manifest = json.loads((folder / "art_direction.json").read_text())
            manifest["style_family"] = "renamed_copy_of_existing"
            (folder / "art_direction.json").write_text(json.dumps(manifest))
            errors = gate_errors(folder, [])
            self.assertTrue(any("outside the registered vocabulary" in e for e in errors), errors)

    def test_pinned_font_refuses_tampered_bytes(self) -> None:
        import art_kit

        with tempfile.TemporaryDirectory() as temporary:
            fonts = Path(temporary)
            shutil.copy(art_kit.ASSET_FONTS / "manifest.json", fonts / "manifest.json")
            (fonts / "Fraunces.ttf").write_bytes(b"not the brand font")
            original = art_kit.ASSET_FONTS
            art_kit.ASSET_FONTS = fonts
            try:
                with self.assertRaises(RuntimeError):
                    art_kit.pinned_font("Fraunces.ttf")
            finally:
                art_kit.ASSET_FONTS = original
        self.assertTrue(Path(art_kit.pinned_font("Fraunces.ttf")).is_file())


class HistoryOrderingTests(unittest.TestCase):
    def _repo_with_refs(self, names: list[tuple[str, str]]) -> Path:
        repo = Path(tempfile.mkdtemp()) / "repo"
        repo.mkdir()
        env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com", "PATH": "/usr/bin:/bin"}

        def git(*args: str) -> None:
            subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, env=env)

        git("init", "-q", "-b", "main")
        (repo / "README").write_text("seed\n")
        git("add", "README")
        git("commit", "-q", "-m", "seed")
        for ref_branch, source in names:
            git("checkout", "-q", "-B", ref_branch, "main")
            (repo / "out").mkdir(exist_ok=True)
            for filename in ("post_image.png", "post_image.png.meta.json", "art_direction.json"):
                shutil.copy(EX / source / filename, repo / "out" / filename)
            git("add", "-f", "out")
            git("commit", "-q", "-m", ref_branch)
            git("update-ref", f"refs/remotes/origin/{ref_branch}", "HEAD")
        git("checkout", "-q", "main")
        return repo

    def test_same_day_numeric_suffixes_sort_and_current_branch_is_excluded(self) -> None:
        repo = self._repo_with_refs([
            ("codex/texas-desk-2026-10-07", STORIES[0]),
            ("codex/texas-desk-2026-10-07-2", STORIES[1]),
            ("codex/texas-desk-2026-10-07-10", STORIES[2]),
            ("codex/texas-desk-2026-10-07-3", STORIES[1]),
        ])
        history = gate.load_history(repo, "2026-10-07")
        refs = [entry["ref"] for entry in history]
        self.assertEqual(refs, [
            "refs/remotes/origin/codex/texas-desk-2026-10-07",
            "refs/remotes/origin/codex/texas-desk-2026-10-07-2",
            "refs/remotes/origin/codex/texas-desk-2026-10-07-3",
            "refs/remotes/origin/codex/texas-desk-2026-10-07-10",
        ])
        excluded = gate.load_history(repo, "2026-10-07", "codex/texas-desk-2026-10-07-10")
        self.assertNotIn("refs/remotes/origin/codex/texas-desk-2026-10-07-10", [e["ref"] for e in excluded])
        window, previous = gate.select_history(history, "2026-10-07")
        self.assertEqual(previous["suffix"], 10)

    def test_unreadable_history_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(gate.HistoryError):
                gate.load_history(Path(temporary), "2026-10-09")


class BuildOrderTests(unittest.TestCase):
    def test_build_orders_hashes_and_resets_review_only_when_pixels_change(self) -> None:
        import build_art

        with tempfile.TemporaryDirectory() as temporary:
            folder = copy_story(STORIES[1], Path(temporary))
            usage = Path(temporary) / "usage.json"
            first = build_art.build(folder, usage, limit=3)
            self.assertFalse(first["review_reset"])
            manifest = json.loads((folder / "art_direction.json").read_text())
            self.assertEqual(manifest["renderer"]["sha256"], gate.sha256_file(folder / "artwork.py"))
            self.assertEqual(json.loads((folder / "post_image.png.meta.json").read_text())["renderer_sha256"],
                             gate.sha256_file(folder / "artwork.py"))
            self.assertTrue((folder / "thumb_300.png").is_file())

            source = (folder / "artwork.py").read_text()
            (folder / "artwork.py").write_text(source.replace("seed=2026", "seed=2027"))
            second = build_art.build(folder, usage, limit=3)
            self.assertTrue(second["review_reset"])
            manifest = json.loads((folder / "art_direction.json").read_text())
            review = manifest["visual_review"]
            self.assertIsNone(review["reviewed_post_image_sha256"])
            self.assertFalse(review["full_size_checked"])
            self.assertFalse(any(review["checks"].values()), "build must never mark a visual check true")
            errors = gate_errors(folder, [])
            self.assertIn("visual review does not match the current final image hash", errors)

            with self.assertRaises(RuntimeError):
                build_art.build(folder, usage, limit=2)


if __name__ == "__main__":
    unittest.main()
