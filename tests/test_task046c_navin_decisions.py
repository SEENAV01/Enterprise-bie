"""Navin's decisions of 29 October 2026 (Task 046 Part C), as code: v1's real-world examples locked in the library and read
FIRST (the AI is not asked for a locked example; the run report counts library hits against AI examples); images made
through the ChatGPT plan allowed in lessons with their provenance; India Code, the SRTM15+ relief and BodyParts3D approved
by name; Hipparcos still waiting with the Yale Bright Star Catalogue as the default star source; Remotion's open decision
closed. Offline: fixtures, no network, no keys, no money.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from bie.brain import content_types as ct, explanations, soul, understanding  # noqa: E402
from bie.toolbox import demos, licence, registry  # noqa: E402

import lock_explanations  # noqa: E402

FAMILY = "economics_commerce_management"
TYPES = ct.load()
NEEDS = lambda item: TYPES.needs_real_world(FAMILY, item.get("content_type", ""))     # noqa: E731
EXAMPLE = {"place": "kirana shop", "actors": ["shopkeeper", "buyer"], "goods": ["sugar"],
           "numbers": [{"what": "price of sugar", "before": "₹40", "after": "₹50"}],
           "steps": [{"step": "the buyer pays ₹40 in notes", "mechanism_link": "accepted as payment"},
                     {"step": "next month the same notes buy less sugar", "mechanism_link": "value changes"}],
           "term_after": "isliye ise medium of exchange kehte hain", "real_life_link": "every purchase at a shop"}


def chapter(item_example=EXAMPLE):
    return {"schema": "bie.brain.chapter-map/2", "course": {"title": "3. Money", "subject": "Indian Economy", "learners": "UPSC aspirants",
                                                           "exam": "UPSC", "language": "Hinglish"},
            "items": {"p001-i3": {"item_id": "p001-i3", "kind": "definition", "content_type": "definition", "teachable": True, "page": 1, "source": "text",
                                  "content": "Money is anything generally accepted as a medium of exchange.",
                                  "unpack": {"terms": [{"term": "medium of exchange", "plain_meaning": "x", "everyday_image": "y"}],
                                             "why_chain": [], "real_world_example": item_example}}},
            "pages": [{"page": 1, "status": "passed", "rounds": 1, "item_ids": ["p001-i3"]}],
            "map": {"concepts": [{"concept_id": "c1", "name": "Money", "item_ids": ["p001-i3"], "content_type": "definition",
                                  "core_explanation": "Money is what people accept as payment."}]}, "map_status": "passed", "cost_usd": 0.0}


class LockedExamples(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "explanations.json"
        self.path.write_text(json.dumps({"schema": explanations.SCHEMA, "version": "2026-10-24.1", "entries": [], "examples": []}), encoding="utf-8")
        explanations.load.cache_clear()

    def tearDown(self):
        explanations.load.cache_clear()
        self.tmp.cleanup()

    def test_the_lock_tool_locks_the_example_not_its_narration_and_points_back_at_the_run(self):
        run = Path(self.tmp.name) / "vm-money-understand"
        run.mkdir()
        (run / "chapter_map.json").write_text(json.dumps(chapter(), ensure_ascii=False), encoding="utf-8")
        code = lock_explanations.main(["--run", str(run), "--items", "p001-i3", "--what", "examples", "--by", "Navin, 29 October 2026", "--path", str(self.path)])
        self.assertEqual(code, 0)
        lib = explanations.load(str(self.path))
        self.assertEqual((len(lib.entries), len(lib.examples)), (0, 1))
        ex = lib.examples[0]
        self.assertEqual((ex.key, ex.term, ex.source, ex.from_run), ("medium of exchange", "medium of exchange", "Navin, 29 October 2026", "vm-money-understand:p001-i3"))
        self.assertEqual(ex.example["place"], "kirana shop")
        self.assertEqual((ex.narration, ex.narration_locked), (None, False))        # the wording waits for the narration work
        self.assertEqual((ex.locked_version, lib.version), ("2026-10-24.2", "2026-10-24.2"))
        self.assertEqual(ex.concepts, ("Money",))
        self.assertIn("narration wording not locked", json.loads(self.path.read_text(encoding="utf-8"))["changes"][0])

    def test_an_item_without_an_example_cannot_be_locked_as_one(self):
        run = Path(self.tmp.name) / "run2"
        run.mkdir()
        (run / "chapter_map.json").write_text(json.dumps(chapter(soul.empty_unpack()["real_world_example"])), encoding="utf-8")
        self.assertEqual(lock_explanations.main(["--run", str(run), "--items", "p001-i3", "--what", "examples", "--by", "x", "--path", str(self.path)]), 2)

    def test_library_first_fills_a_locked_example_by_code_and_counts_hits_against_ai(self):
        explanations.lock_examples_from_items(chapter(), ["p001-i3"], by="Navin, 29 October 2026", run="vm-money-understand", path=str(self.path))
        lib = explanations.load(str(self.path))
        page_text = "Money is anything generally accepted as a medium of exchange. Barter needs a double coincidence of wants."
        found = lib.lookup_examples(page_text)
        self.assertEqual([e.key for e in found], ["medium of exchange"])
        self.assertTrue(lib.example_lines(page_text).startswith("  locked real-world example | medium of exchange: place kirana shop; actors shopkeeper, buyer"))
        maker = [{"item_id": "i1", "content_type": "definition", "content": "Money is a medium of exchange.",
                  "unpack": {"terms": [{"term": "medium of exchange", "plain_meaning": "", "everyday_image": ""}], "why_chain": [],
                             "real_world_example": dict(EXAMPLE, place="a different shop the AI invented")}},
                 {"item_id": "i2", "content_type": "cause_effect", "content": "Barter fails without a double coincidence of wants.",
                  "unpack": {"terms": [{"term": "double coincidence of wants", "plain_meaning": "", "everyday_image": ""}], "why_chain": [],
                             "real_world_example": dict(EXAMPLE, place="a village haat")}},
                 {"item_id": "i3", "content_type": "fact_list", "content": "Money has five characteristics.", "unpack": soul.empty_unpack()}]
        counts = explanations.apply_examples(maker, found, needs_example=NEEDS)
        self.assertEqual(counts, {"library": 1, "ai": 1})
        self.assertEqual(maker[0]["unpack"]["real_world_example"]["place"], "kirana shop")       # the library wins over the AI's own
        self.assertEqual(maker[0]["example_source"], "library:medium of exchange")
        self.assertEqual(maker[1]["example_source"], "ai")
        self.assertNotIn("example_source", maker[2])                                             # a fact list takes no example
        self.assertEqual(soul.real_world_problems(maker[0], family=FAMILY, types=TYPES), [])      # S1-16 passes on the locked one

    def test_the_report_names_the_source_and_the_counts(self):
        chap = chapter()
        chap["items"]["p001-i3"]["example_source"] = "library:medium of exchange"
        chap["items"]["p001-i4"] = dict(chap["items"]["p001-i3"], item_id="p001-i4", example_source="ai",
                                        content="Acceptability means people take it as payment.",
                                        unpack=dict(chap["items"]["p001-i3"]["unpack"], terms=[{"term": "Acceptability", "plain_meaning": "", "everyday_image": ""}]))
        chap["pages"][0]["item_ids"].append("p001-i4")
        chap["quality"] = understanding.quality(chap)
        self.assertEqual((chap["quality"]["real_world_from_library"], chap["quality"]["real_world_from_ai"]), (1, 1))
        md = understanding.render_markdown(dict(chap, rulebook_version="x", maker_route="codex", reviewer_route="codex", level="upsc_pcs",
                                                content_types_version="x"))
        self.assertIn("1 from BIE's locked library (no AI asked), 1 from the AI", md)
        self.assertIn("| library |", md)
        self.assertIn("| AI |", md)


class TheRealLibrary(unittest.TestCase):
    def test_v1s_examples_are_locked_and_found_again(self):
        lib = explanations.load()
        locked = [e for e in lib.examples if e.from_run.startswith("vm-t046c-money-understand-d-brain-understand:")]
        self.assertEqual(len(locked), 11)                 # the 11 of v1's 13 items that carry an example (two list items take none)
        self.assertTrue(all(e.source == "Navin, 29 October 2026" for e in locked))
        # the narration wording of all 11 locked on 29 October 2026 after the narration work, from v1 of the lesson resume -e
        self.assertTrue(all(e.narration_locked and e.narration["video_id"] == "v1" and e.narration["beats"] for e in locked))
        self.assertEqual({e.narration_version for e in locked}, {"2026-10-24.3"})
        self.assertEqual(sum(len(e.narration["beats"]) for e in locked), 42)
        self.assertEqual({e.key for e in locked} & {"medium of exchange", "acceptability", "durability", "portability", "divisibility"},
                         {"medium of exchange", "acceptability", "durability", "portability", "divisibility"})
        found = lib.lookup_examples("Durability: money must not wear out; portability: easy to carry; a medium of exchange.")
        self.assertEqual({e.key for e in found} >= {"durability", "portability", "medium of exchange"}, True)
        self.assertEqual(lib.lookup_examples("Epithelium lines absorptive surfaces."), [])     # another subject: no hit, no change


class GeneratedImages(unittest.TestCase):
    def test_a_route_2_image_is_allowed_with_its_provenance_and_refused_without(self):
        image = {"asset_id": "i1", "title": "a cell", "source": "bie_chatgpt_plan", "generated_by": "generated by BIE through the ChatGPT plan",
                 "prompt": "a squamous epithelial cell sheet, wet, translucent", "generated_on": "2026-10-29"}
        verdict = licence.asset_verdict(image)
        self.assertTrue(verdict.allowed)
        self.assertEqual((verdict.licence_class, verdict.basis), ("generated", "own"))
        self.assertIn("Navin, 2026-10-29", verdict.reason)
        bare = licence.asset_verdict({"asset_id": "i2", "title": "x", "source": "openai-image-gen"})
        self.assertEqual(bare.verdict, "refused")
        self.assertIn("missing: generated_by, prompt, generated_on", bare.reason)
        self.assertEqual(licence.policy()["generated_images"]["decided"]["by"], "Navin")

    def test_the_image_job_writes_the_provenance_on_every_made_image(self):
        spec = importlib.util.spec_from_file_location("vm_image", ROOT / "tools" / "vm_image.py")
        vm_image = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(vm_image)
        client = mock.Mock()
        client.login_status.return_value = {"logged_in": True}
        client.plan_usage.return_value = {}
        client.generate_image.return_value = {"path": "images/a.png", "bytes": 10}
        out = Path(tempfile.mkdtemp()) / "run"
        summary = vm_image.run({"prompts": [{"id": "a", "prompt": "a cell sheet"}]}, out, client=client)
        row = summary["images"][0]
        self.assertEqual((row["status"], row["source"], row["generated_by"], row["prompt"]),
                         ("made", "bie_chatgpt_plan", "generated by BIE through the ChatGPT plan", "a cell sheet"))
        self.assertRegex(row["generated_on"], r"^\d{4}-\d{2}-\d{2}$")
        self.assertTrue(licence.asset_verdict(dict(row, asset_id="a", title="a")).allowed)


class Licences(unittest.TestCase):
    def test_navins_approvals_of_29_october_open_three_sources_with_a_credit(self):
        pol = licence.policy()
        self.assertEqual(pol["version"], "2026-10-29.1")
        approved = {a["id"]: a for a in pol["sources"]["approved_by_navin"]}
        self.assertEqual(set(approved), {"india-code", "gmt-earth-relief", "bodyparts3d"})
        self.assertTrue(all(a["approved_on"] == "2026-10-29" and a["words"] and a["condition"] for a in approved.values()))
        verdicts = {t.id: licence.tool_verdict(t) for t in registry.load().tools}
        for tid in ("india-code", "gmt-earth-relief", "bodyparts3d"):
            self.assertEqual(verdicts[tid].verdict, "allowed", tid)
            self.assertTrue(verdicts[tid].credit_required, tid)
        self.assertEqual(verdicts["hipparcos"].verdict, "needs_navin")
        self.assertEqual(verdicts["yale-bsc"].verdict, "allowed")
        self.assertFalse(verdicts["yale-bsc"].credit_required)
        act = {"asset_id": "a3", "title": "BNSS (India Code)", "source": "india_code", "licence": "Government of India content from India Code",
               "licence_url": "https://indiacode.gov.in", "author": "Legislative Department", "page_url": "https://indiacode.gov.in/handle/1"}
        self.assertTrue(licence.asset_verdict(act).allowed)
        self.assertIn("missing: author", licence.asset_verdict(dict(act, author="")).reason)   # approved, but the source must be acknowledged
        self.assertEqual(licence.policy_problems(pol), [])

    def test_hipparcos_waits_the_boundary_keeps_its_condition_and_remotion_is_decided(self):
        pol = licence.policy()
        hip = next(s for s in pol["sources"]["needs_navin"] if s["id"] == "hipparcos")
        self.assertIn("ESA's commercial terms still apply", hip["why"])
        self.assertEqual(pol["india_boundary"]["verdict"], "needs_navin")
        self.assertIsNone(pol["india_boundary"]["approved_boundary"])
        self.assertIn("Survey of India", pol["india_boundary"]["navin_condition"]["procedure"])
        self.assertEqual(pol["software"]["open_decisions"], [])
        self.assertEqual(pol["software"]["decided"][0]["id"], "remotion")
        self.assertIn("decided by Navin on 2026-10-29", licence.tool_verdict(registry.load().tool("remotion")).note)

    def test_the_sky_demo_now_uses_the_yale_catalogue_and_is_lesson_allowed(self):
        demo = demos.by_id("astro-sky")
        self.assertIn("yale-bsc", demo.tools)
        self.assertNotIn("hipparcos", demo.tools)
        self.assertEqual(demos.lesson_use(demo.tools)["use"], "lessons")
        tool = registry.load().tool("yale-bsc")
        self.assertEqual((tool.licence, tool.status), ("Public domain", "demo_proven"))


class YaleCatalogue(unittest.TestCase):
    def test_the_fixed_width_parser_reads_sirius_right(self):
        from bie.toolbox.adapters import astro                     # the parser is pure Python: the canonical gate has no pandas
        rows = {r["hr"]: r for r in astro.load_bsc(ROOT / "tests" / "toolbox" / "fixtures" / "bsc5_3stars.dat")}
        self.assertEqual(sorted(rows), [1713, 2061, 2491])
        sirius = rows[2491]
        self.assertAlmostEqual(sirius["ra_hours"], 6 + 45 / 60 + 8.9 / 3600, places=5)
        self.assertAlmostEqual(sirius["dec_degrees"], -(16 + 42 / 60 + 58 / 3600), places=5)
        self.assertEqual((sirius["magnitude"], sirius["epoch_year"], sirius["parallax_mas"]), (-1.46, 2000.0, 0.0))
        self.assertAlmostEqual(sirius["ra_mas_per_year"], -553.0)
        self.assertAlmostEqual(sirius["dec_mas_per_year"], -1205.0)
        self.assertEqual(rows[2061]["name"], "58Alp Ori")
        self.assertEqual(list(astro.BSC_COLUMNS), ["hr", "name", "ra_h", "ra_m", "ra_s", "de_sign", "de_d", "de_m", "de_s", "vmag", "pm_ra", "pm_de"])


if __name__ == "__main__":
    unittest.main()
