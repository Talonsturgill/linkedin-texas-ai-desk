from __future__ import annotations

import datetime as dt
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / ".agents/skills/texas-desk-artwork/scripts"))

from build_email import build_payload, render_html  # noqa: E402
from check_config import validate as validate_config  # noqa: E402
from check_post import validate_post  # noqa: E402
from history_scan import summarize  # noqa: E402
from qa_check import validate as validate_artwork  # noqa: E402
from compose_cover import compose  # noqa: E402
from validate_run import validate as validate_run  # noqa: E402
from check_score import validate_score  # noqa: E402
from prose_rules import check_prose  # noqa: E402
from runtime_check import assess  # noqa: E402
from gmail_account import resolve_account  # noqa: E402


def base_dossier() -> dict:
    return {
        "schema_version": 1,
        "run_date": "2026-09-02",
        "window_days": 60,
        "no_target_this_cycle": False,
        "selected_subject": {
            "full_name": "Riley Chen",
            "role": "Executive director",
            "organization": "Texas Robotics Lab",
            "role_category": "research",
            "texas_tie": "A Travis County pilot",
            "place_label": "TRAVIS COUNTY",
            "coordinates": "30 N 97 W",
            "role_source": {
                "url": "https://example.edu/role",
                "title": "Leadership",
                "publisher": "Example University",
            },
            "verbatim_quotes": [],
        },
        "selected_decision": {
            "what_happened": "Riley Chen chose a regional robotics pilot.",
            "decision_anchor": "regional robotics pilot",
            "date": "2026-09-02",
            "owner_evidence": "The signed notice names Riley Chen as decision owner.",
            "alternative_available": "A laboratory-only program remained available.",
            "ai_nexus": "The pilot deploys machine perception in public facilities.",
            "texas_consequence": "Travis County operators will measure reliability.",
            "next_check": "The first reliability report is due in winter.",
            "public_policy_or_electoral": False,
            "primary_source": {
                "url": "https://example.edu/notice",
                "title": "Pilot notice",
                "publisher": "Example University",
                "published_at": "2026-09-02",
                "source_type": "primary",
                "claims_supported": ["decision", "date", "owner"],
            },
            "corroborating_sources": [{
                "url": "https://example.news/pilot",
                "title": "County robotics pilot",
                "publisher": "Example News",
                "published_at": "2026-09-02",
                "source_type": "independent_reporting",
                "independent_of_subject": True,
                "claims_supported": ["pilot", "county consequence"],
            }],
        },
        "analysis": {
            "editorial_mode": "execution_assessment",
            "assessment": "sharp",
            "evidence_for": ["The pilot has a named operator and measure."],
            "evidence_against": ["Results are not yet public."],
            "structural_read": "The decision moves testing into operating conditions.",
            "forward_implication": "The report will show whether expansion is justified.",
            "conflict_screen": "clear",
        },
        "required_post_phrases": ["Riley Chen", "regional robotics pilot"],
        "verified_facts": [{
            "claim": "Riley Chen chose a regional robotics pilot on 2026-09-02.",
            "source_urls": ["https://example.edu/notice", "https://example.news/pilot"],
        }],
        "gate_results": {
            "named_subject": True,
            "recent_decision": True,
            "decision_owner": True,
            "texas_ai_consequence": True,
            "primary_source": True,
            "independent_corroboration": True,
            "position_or_accountability_read": True,
            "not_recent_repeat": True,
            "conflict_clear": True,
            "political_neutrality": True,
        },
        "dropped_candidates": [],
    }


def valid_post() -> str:
    paragraphs = [
        "Riley Chen chose a regional robotics pilot on September 2nd, 2026.",
        "The choice puts Texas Robotics Lab inside Travis County operations.",
        (
            "The practical case is clear. A laboratory can prove that a model works under controlled "
            "conditions. A county facility exposes the harder questions around staffing, maintenance, "
            "procurement, and reliability. Chen had a laboratory-only path available and chose the "
            "operating environment instead."
        ),
        (
            "That is a defensible execution choice because the pilot has a named owner, a defined place, "
            "and a result that local operators can inspect. It also shifts part of the burden from a "
            "research team to people responsible for daily service. Their experience should guide the "
            "pilot alongside a benchmark produced before deployment."
        ),
        (
            "The constraint is evidence. The announcement establishes the pilot and its ownership, but it "
            "does not establish durable performance. Texas Robotics Lab still has to show how failures are "
            "reported, how operators can stop the system, and whether the measured benefit survives ordinary "
            "working conditions."
        ),
        (
            "The next check is the first reliability report. It should separate technical accuracy from "
            "operational usefulness and explain what changed after staff feedback. Without that record, "
            "expansion would move faster than the evidence. With it, other Texas institutions would have a "
            "usable basis for deciding whether the approach travels."
        ),
    ]
    filler = (
        "The useful standard is not novelty. It is whether the work gives Texas operators a clearer choice, "
        "a visible safeguard, and evidence that can survive outside the laboratory."
    )
    text = "\n\n".join(paragraphs)
    while len(text.split()) < 337:
        text += "\n\n" + filler
    text += "\n\nWhat should the reliability report disclose before this pilot expands?"
    return text + "\n\n#TexasAI #TexasResearch #ResponsibleAI\n"


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.brand = yaml.safe_load((ROOT / "config/brand.yaml").read_text(encoding="utf-8"))

    def test_versioned_configuration(self) -> None:
        self.assertEqual(validate_config(), [])

    def test_valid_post_passes_and_ungrounded_number_fails(self) -> None:
        dossier = base_dossier()
        report = validate_post(valid_post(), dossier, self.brand)
        self.assertTrue(report["ok"], report["errors"])

        bad = valid_post().replace(
            "What should the reliability report",
            "A 77-day promise is unsupported.\n\nWhat should the reliability report",
        )
        bad_report = validate_post(bad, dossier, self.brand)
        self.assertIn("numeral is not grounded in dossier: 77", bad_report["errors"])

    def test_public_policy_requires_neutral_mode(self) -> None:
        dossier = base_dossier()
        dossier["selected_decision"]["public_policy_or_electoral"] = True
        report = validate_post(valid_post(), dossier, self.brand)
        self.assertIn(
            "public-policy decision must use neutral_accountability mode", report["errors"]
        )
        self.assertIn(
            "public-policy decision cannot receive an editorial rating", report["errors"]
        )

    def test_email_escapes_copy_and_has_connector_shape(self) -> None:
        dossier = base_dossier()
        dossier["selected_subject"]["organization"] = "Texas <Robotics> Lab"
        html_body = render_html(
            post="Use <care> & verify.",
            image_url=(
                "https://raw.githubusercontent.com/Talonsturgill/linkedin-texas-ai-desk/"
                + "a" * 40 + "/out/post_image.png"
            ),
            dossier=dossier,
            score={"ship": True, "criteria": [], "weighted_total": 9, "threshold": 8},
            date="September 2nd, 2026",
            branch="codex/texas-desk-2026-09-02",
            commit="a" * 40,
            editor_note="Ready <for review>",
        )
        self.assertIn("Use &lt;care&gt; &amp; verify.", html_body)
        self.assertIn("Ready &lt;for review&gt;", html_body)
        self.assertNotIn("Use <care>", html_body)
        payload = build_payload(
            to="editor@example.com", subject="Texas Desk", html_body=html_body
        )
        self.assertEqual(payload["payload"]["mime_type"], "text/html")
        with self.assertRaises(ValueError):
            build_payload(to="not-an-address", subject="x", html_body="x")

    def test_history_cooldown_and_permanent_pair(self) -> None:
        records = [
            ("origin/codex/texas-desk-2026-09-01", base_dossier()),
            ("origin/codex/texas-desk-2026-07-01", base_dossier()),
        ]
        result = summarize(records, dt.date(2026, 9, 2), 21)
        self.assertEqual(len(result["recent_subjects"]), 1)
        self.assertEqual(len(result["covered_subject_decision_pairs"]), 1)
        self.assertEqual(result["recent_subjects"][0]["subject"], "Riley Chen")

    def test_complete_profile_package_passes_run_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            (target / "desk_dossier.json").write_text(
                json.dumps(base_dossier()), encoding="utf-8"
            )
            (target / "final_post.md").write_text(valid_post(), encoding="utf-8")
            criteria = [
                {"name": row["name"], "weight": row["weight"], "score": 9, "notes": "Pass"}
                for row in yaml.safe_load(
                    (ROOT / "config/rubric.yaml").read_text(encoding="utf-8")
                )["rubric"]["criteria"]
            ]
            (target / "score_report.json").write_text(
                json.dumps({
                    "ship": True,
                    "weighted_total": 9.0,
                    "threshold": 8.0,
                    "hard_failures": [],
                    "hard_fail_checks": {
                        row["name"]: True for row in yaml.safe_load(
                            (ROOT / "config/rubric.yaml").read_text()
                        )["rubric"]["hard_fail_checks"]
                    },
                    "criteria": criteria,
                }),
                encoding="utf-8",
            )
            report = validate_run(target, history_root=str(ROOT))
            self.assertFalse(report["ok"])
            self.assertTrue(report["errors"], "profile without coded artwork must not pass")
            self.assertTrue(
                all("post_image" in error or "artwork" in error or "missing" in error
                    for error in report["errors"]),
                report["errors"],
            )

    def test_runtime_fails_closed_before_research(self) -> None:
        runtime = json.loads((ROOT / "config/runtime.json").read_text())
        states = {name: "available" for name in runtime["required_capabilities"]}
        self.assertTrue(assess(states, runtime)["ok"])
        for missing in ("unavailable", "unknown"):
            states["coded_art"] = missing
            result = assess(states, runtime)
            self.assertEqual(result["state"], "needs-attention")
            self.assertEqual(result["missing"], ["coded_art"])
            self.assertIsNone(result["measured_cost_usd"])

    def test_connected_account_requires_trusted_matching_metadata(self) -> None:
        self.assertEqual(resolve_account({"profile": {"emailAddress": "editor@example.com"}})["email"],
                         "editor@example.com")
        self.assertEqual(resolve_account({"connector_view_urls": [
            "https://mail.google.com/mail/?authuser=editor%40example.com"]})["email"],
            "editor@example.com")
        for evidence in (
            {"session_email": "editor@example.com"},
            {"connector_view_urls": ["https://example.com/?authuser=editor@example.com"]},
            {"connector_view_urls": ["https://mail.google.com/mail/?authuser=0"]},
            {"profile": {"emailAddress": "editor@example.com"}, "connector_view_urls": [
                "https://mail.google.com/mail/?authuser=another@example.com"]},
        ):
            with self.assertRaises(ValueError):
                resolve_account(evidence)

    def test_personal_rule_is_case_insensitive_and_whole_word(self) -> None:
        for word in ("matter", "MATTERS", "Mattered", "mattering"):
            self.assertTrue(check_prose("The word is " + word + "."))
        self.assertEqual(check_prose("Material choices and antimatter research."), [])
        self.assertEqual(check_prose("Source https://example.org/matter/report"), [])
        bad = valid_post().replace("The constraint is evidence.", "This MATTERS.")
        self.assertIn("prohibited whole word: matters",
                      validate_post(bad, base_dossier(), self.brand)["errors"])

    def test_email_rejects_prohibited_editor_prose(self) -> None:
        with self.assertRaises(ValueError):
            render_html(post="Clean post.", image_url="", dossier=base_dossier(),
                        score={}, date="October 9th, 2026", branch="test", commit="a" * 40,
                        editor_note="This matters.")

    def test_score_recomputes_and_requires_complete_rubric(self) -> None:
        rubric = yaml.safe_load((ROOT / "config/rubric.yaml").read_text())["rubric"]
        good = {
            "ship": True, "weighted_total": 9.0, "threshold": 8.0,
            "hard_failures": [],
            "hard_fail_checks": {row["name"]: True for row in rubric["hard_fail_checks"]},
            "criteria": [{**row, "score": 9, "notes": "Verified in dossier."}
                         for row in rubric["criteria"]],
        }
        self.assertEqual(validate_score(good, rubric), [])
        for mutate in (
            lambda s: s.update(weighted_total=10),
            lambda s: s.update(criteria=[]),
            lambda s: s.update(hard_fail_checks={}),
            lambda s: s["criteria"][0].update(score=float("nan")),
            lambda s: s["criteria"][0].update(weight=1),
            lambda s: s["criteria"][0].update(score=11),
        ):
            candidate = json.loads(json.dumps(good))
            mutate(candidate)
            self.assertTrue(validate_score(candidate, rubric))

    def test_no_target_package_requires_drop_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            dossier = {
                "schema_version": 1,
                "run_date": "2026-09-02",
                "window_days": 90,
                "no_target_this_cycle": True,
                "_validation_note": "No candidate cleared independent corroboration.",
                "dropped_candidates": [],
            }
            (target / "desk_dossier.json").write_text(
                json.dumps(dossier), encoding="utf-8"
            )
            report = validate_run(target)
            self.assertFalse(report["ok"])
            self.assertIn(
                "no-target dossier needs a nonempty dropped_candidates list", report["errors"]
            )

    def test_coded_compose_requires_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            base = target / "base.png"
            base.write_bytes((ROOT / "examples/coded_art/fermi_tensorwave_2026-10-07/art_base.png").read_bytes())
            with self.assertRaises(ValueError):
                compose(
                    base_path=base, headline="Coded provenance", role="RESEARCH",
                    date="SEPTEMBER 2ND, 2026", place="TRAVIS COUNTY", coords="",
                    source="coded", out_path=target / "final.png",
                )
            with self.assertRaises(ValueError):
                compose(
                    base_path=base, headline="Coded provenance", role="RESEARCH",
                    date="SEPTEMBER 2ND, 2026", place="TRAVIS COUNTY", coords="",
                    source="fallback", out_path=target / "final.png",
                )
            fixture = ROOT / "examples/coded_art/fermi_tensorwave_2026-10-07"
            compose(
                base_path=fixture / "art_base.png", headline="Coded provenance", role="OPERATOR",
                date="OCTOBER 7TH, 2026", place="CARSON COUNTY", coords="", source="coded",
                out_path=target / "final.png", art_direction=fixture / "art_direction.json",
                renderer=fixture / "artwork.py", dossier=fixture / "desk_dossier.json",
            )
            meta = json.loads((target / "final.png.meta.json").read_text())
            self.assertEqual(meta["source"], "coded")
            self.assertEqual(validate_artwork(target / "final.png", "OCTOBER 7TH, 2026", "TEXAS DESK"), [])

if __name__ == "__main__":
    unittest.main()
