"""Task 046 Part C addition (Navin, 27 October 2026): economics concepts are applied in a real Indian situation before they
are named ("demand pull inflation wale concept ko dukandar, bazar, log, sugar wale example se samjhaya tha").

The rulebook carries the method (teacher_examples.json) and the slot (content_types.json); Section 1 checks the slot
(S1-16), Section 2 checks that the example runs first with its numbers (S2-08), the reviewer's checklist carries both, the
director makes the example's beats a story piece (world mode when a kit exists, else a canvas with crowd, value and icon
elements and a missing-kit line), and the fake maker answers all of it offline. Everything below is test input, never
lesson content.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

import test_task045_cards as t045  # noqa: E402
import test_task046_canvas_director as tcd  # noqa: E402
from bie.brain import canvas_director as cd, content_types as ct, fake, lesson, regression, rulebook, soul, understanding  # noqa: E402
from bie.brain.common import checklist_text  # noqa: E402
from bie.brain.pages import Block, Page  # noqa: E402
from bie.brain.understanding import Course  # noqa: E402
from bie.brain.video import world  # noqa: E402

ECON = "economics_commerce_management"
BIO = "biology_medical"
TYPES = ct.load()
BOOK = rulebook.load()
COURSE = Course(title="3. Money", subject="Indian Economy", learners="UPSC / State PCS aspirants", exam="UPSC / State PCS",
                language="Hinglish", level="upsc_pcs")


def example(**over):
    base = {"place": "kirana shop", "actors": ["shopkeeper", "buyers"], "goods": ["sugar"],
            "numbers": [{"what": "price", "before": "₹50", "after": "₹65"}, {"what": "buyers", "before": "2", "after": "12"}],
            "steps": [{"step": "3 packet, ₹50 ka ek; kal 2 khareedar", "mechanism_link": "supply fixed, demand low"},
                      {"step": "aaj 12 khareedar; daam ₹65", "mechanism_link": "demand above supply, price up"}],
            "term_after": "isliye ise demand-pull inflation kehte hain", "real_life_link": "Diwali se pehle sabzi mandi"}
    base.update(over)
    return base


def econ_item(iid="i1", kind="definition", ex=None):
    item = dict(t045.item(iid, ["p0001-b0001"], kind, "what", "evidence", "why"), content="Demand-pull inflation is a rise in prices.")
    item["unpack"] = {"terms": [{"term": "demand-pull inflation", "plain_meaning": "माँग बढ़ने से दाम बढ़ना", "everyday_image": "मंडी"}],
                      "why_chain": [{"step": "लोग ज़्यादा, माल उतना ही", "basis": "book"}], "example_or_place": "", "consequence": "",
                      "visual_verb": "", "level_extra": "", "real_world_example": ex if ex is not None else example()}
    return item


class Rulebook(unittest.TestCase):
    def test_the_method_the_slot_and_the_rules_are_in_the_rulebook(self):
        bank = soul.load_teacher()
        self.assertEqual(bank["version"], "2026-10-27.1")
        method = next(m for m in bank["methods"] if m["id"] == "real_world_application")
        self.assertIn("Isliye ise demand-pull inflation kehte hain", method["example"])
        self.assertIn("real_world_application", bank["changes"][0])
        self.assertIn("kirana shop", soul.teacher_text())
        self.assertEqual(TYPES.real_world.types, ("definition", "cause_effect", "process"))
        self.assertEqual(TYPES.real_world.families, (ECON,))
        self.assertTrue(TYPES.needs_real_world(ECON, "definition") and TYPES.needs_real_world(ECON, "process"))
        self.assertFalse(TYPES.needs_real_world(BIO, "definition") or TYPES.needs_real_world(ECON, "figure"))
        rules = {r.id: r for r in BOOK.rules}
        self.assertEqual((rules["S1-16"].status, rules["S1-16"].sections), ("locked", ("understand",)))
        self.assertEqual((rules["S2-08"].status, rules["S2-08"].sections), ("locked", ("lesson",)))
        self.assertIn("sugar", rules["S1-16"].rule)
        for name in ("vision-2026-10-21@2026-10-21.14", "content_types@2026-10-27.1", "teacher_examples@2026-10-27.1", "simple_hindi@2026-10-27.1"):
            self.assertIn(name, BOOK.version)
        self.assertIn("S1-16", checklist_text(BOOK, "understand"))          # the reviewer answers it on every page
        self.assertIn("S2-08", checklist_text(BOOK, "lesson"))
        changes = {c["rule"]: c for c in regression.RULE_CHANGES}
        self.assertTrue(changes["S1-16"]["match"].search("item p001-i1: real_world_example.place is empty (S1-16)"))
        self.assertTrue(changes["S2-08"]["match"].search("beat b4: names 'x' before its real-world example runs (beat b2) (S2-08)"))

    def test_the_method_and_the_slot_reach_both_prefixes(self):
        page_text = understanding.page_prefixes(COURSE, BOOK)[0].text
        self.assertIn("unpack.real_world_example (S1-16", page_text)
        self.assertIn("Apply it in the real world first, then name it", page_text)
        script_text = lesson.script_prefixes(COURSE, BOOK)[0].text
        self.assertIn("Real-world application (S2-08", script_text)
        self.assertIn("kirana shop", script_text)
        review = lesson.script_prefixes(COURSE, BOOK)[1].text
        self.assertIn("economically correct", review)
        self.assertIn("(S1-16); report it under wrong", understanding.page_prefixes(COURSE, BOOK)[1].text)


class UnpackCheck(unittest.TestCase):
    def test_an_economics_concept_item_needs_the_slot_and_a_full_one_passes(self):
        self.assertEqual(soul.real_world_problems(econ_item(), family=ECON, types=TYPES), [])
        problems = soul.real_world_problems(econ_item(ex=soul.EMPTY_REAL_WORLD), family=ECON, types=TYPES)
        self.assertEqual(len(problems), 1)
        self.assertIn("sugar shop (S1-16)", problems[0])
        self.assertEqual(soul.real_world_problems(econ_item(ex=soul.EMPTY_REAL_WORLD), family=BIO, types=TYPES), [])
        self.assertEqual(soul.real_world_problems(econ_item(kind="figure", ex=soul.EMPTY_REAL_WORLD), family=ECON, types=TYPES), [])
        self.assertEqual(soul.real_world_problems(econ_item(kind="process"), family=ECON, types=TYPES), [])

    def test_each_missing_part_is_named(self):
        def first(**over):
            problems = soul.real_world_problems(econ_item(ex=example(**over)), family=ECON, types=TYPES)
            self.assertEqual(len(problems), 1, problems)
            self.assertTrue(problems[0].endswith("(S1-16)"))
            return problems[0]
        self.assertIn("place is empty", first(place=" "))
        self.assertIn("at least one actor", first(actors=[]))
        self.assertIn("real goods or money", first(goods=[""]))
        self.assertIn("number that changes", first(numbers=[{"what": "price", "before": "₹50", "after": "₹50"}]))
        self.assertIn("number that changes", first(numbers=[{"what": "price", "before": "kam", "after": "zyada"}]))
        self.assertIn("at least two steps", first(steps=[{"step": "one", "mechanism_link": "x"}]))
        self.assertIn("mechanism_link", first(steps=[{"step": "one", "mechanism_link": "x"}, {"step": "two", "mechanism_link": ""}]))
        self.assertIn("term_after", first(term_after=""))
        self.assertIn("real_life_link", first(real_life_link=""))

    def test_check_page_sends_an_economics_item_back_without_its_example(self):
        page = Page(1, (Block("p0001-b0001", "Demand-pull inflation is a rise in prices.", (0, 0, 1, 1)),))
        value = {"notes": {}, "page_summary": "", "boilerplate_block_ids": [], "text_image_disagreements": [],
                 "items": [econ_item(ex=soul.EMPTY_REAL_WORLD)]}
        self.assertTrue(any("(S1-16)" in p for p in understanding.check_page(value, page, family=ECON)))
        self.assertEqual([p for p in understanding.check_page(value, page, family=BIO) if "S1-16" in p], [])
        self.assertEqual([p for p in understanding.check_page(value, page) if "S1-16" in p], [])           # no family: not judged
        value["items"][0]["unpack"]["real_world_example"] = example()
        self.assertEqual([p for p in understanding.check_page(value, page, family=ECON) if "S1-16" in p], [])

    def test_the_example_reaches_the_script_source_the_pages_and_the_map(self):
        lines = soul.unpack_lines(econ_item()["unpack"])
        self.assertTrue(any(l.startswith("  real world (run it first, with these numbers, then name the term) | place: kirana shop") for l in lines))
        self.assertIn("    step 2 | aaj 12 khareedar; daam ₹65 | shows: demand above supply, price up", lines)
        self.assertEqual(soul.real_world_short(example()), "kirana shop · shopkeeper, buyers · sugar · price ₹50 → ₹65; buyers 2 → 12 · 2 steps")
        self.assertEqual(soul.real_world_short(soul.EMPTY_REAL_WORLD), "")
        self.assertEqual(soul.real_world_numbers(example()), {"50", "65", "2", "12"})
        chapter = t045.small_chapter()
        chapter["course"] = dict(chapter["course"], subject="Indian Economy")
        chapter["items"]["p001-i1"]["unpack"]["real_world_example"] = example()
        chapter["items"]["p001-i1"]["content_type"] = "definition"
        chapter["pages"] = [{"page": 1, "status": "passed", "rounds": 1, "summary": "", "last_problems": [], "cost_usd": 0.0,
                             "item_ids": sorted(chapter["items"])}]
        chapter.update(cost_usd=0.0, map_status="passed")
        rows = understanding.real_world_rows(chapter)
        self.assertEqual([(r["item_id"], r["ok"], r["first_try"]) for r in rows if r["item_id"] == "p001-i1"], [("p001-i1", True, True)])
        quality = understanding.quality(chapter)
        self.assertGreaterEqual(quality["real_world_needed"], 1)
        self.assertEqual(quality["real_world_ok"], quality["real_world_filled"])
        self.assertLess(quality["real_world_ok"], quality["real_world_needed"])        # the other economics items carry none
        self.assertIn("real world (run it first", understanding.render_pages(chapter))


def beat(bid, say, covers=("i1",), purpose="explain"):
    return {"beat_id": bid, "part_id": "c1.1", "step": 1, "purpose": purpose, "say": say, "covers_item_ids": list(covers),
            "answers": [], "on_screen": "", "basis": "book"}


GOOD_ORDER = [beat("b1", "दाम अचानक क्यों बढ़ जाते हैं?"),
              beat("b2", "दुकान में चीनी के 3 packet हैं, ₹50 का एक; कल 2 ग्राहक आए।", purpose="story"),
              beat("b3", "आज 12 ग्राहक आ गए, तो दाम ₹65 हो गया।", purpose="story"),
              beat("b4", "इसलिए इसे demand-pull inflation कहते हैं।")]
PARTS = [{"part_id": "c1.1", "type": "definition", "item_ids": ["i1"]}]


class ScriptCheck(unittest.TestCase):
    def test_the_example_runs_first_then_the_term(self):
        items = {"i1": econ_item()}
        self.assertEqual(soul.example_order_problems(GOOD_ORDER, items, PARTS, family=ECON, types=TYPES), [])
        row = soul.example_order_report(GOOD_ORDER, items, PARTS, family=ECON, types=TYPES)[0]
        self.assertEqual((row["example_beats"], row["term_beat"], row["term"], row["ok"]), (["b2", "b3"], "b4", "demand-pull inflation", True))

    def test_the_term_named_before_the_story_goes_back(self):
        items = {"i1": econ_item()}
        beats = [GOOD_ORDER[0], GOOD_ORDER[3], GOOD_ORDER[1], GOOD_ORDER[2]]
        problems = soul.example_order_problems(beats, items, PARTS, family=ECON, types=TYPES)
        self.assertEqual(len(problems), 1)
        self.assertIn("beat b4: names 'demand-pull inflation' before its real-world example runs (beat b2)", problems[0])
        self.assertTrue(problems[0].endswith("(S2-08)"))

    def test_a_story_without_the_numbers_goes_back(self):
        items = {"i1": econ_item()}
        beats = [GOOD_ORDER[0], beat("b2", "दुकान में भीड़ बढ़ी तो दाम बढ़ गया।", purpose="story"), GOOD_ORDER[3]]
        problems = soul.example_order_problems(beats, items, PARTS, family=ECON, types=TYPES)
        self.assertEqual(len(problems), 1)
        self.assertIn("run by no beat that covers it", problems[0])
        self.assertIn("numbers 12, 2, 50, 65", problems[0])

    def test_another_subject_or_an_item_without_an_example_is_not_judged_here(self):
        beats = [GOOD_ORDER[0], GOOD_ORDER[3]]
        self.assertEqual(soul.example_order_problems(beats, {"i1": econ_item()}, PARTS, family=BIO, types=TYPES), [])
        self.assertEqual(soul.example_order_problems(beats, {"i1": econ_item(ex=soul.EMPTY_REAL_WORLD)}, PARTS, family=ECON, types=TYPES), [])
        self.assertEqual(soul.example_order_report([], {"i1": econ_item()}, PARTS, family=ECON, types=TYPES), [])


class Director(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def lesson(self, ex):
        chapter, lesson_ = tcd.econ_lesson()
        chapter["items"]["i1"]["unpack"] = econ_item(ex=ex)["unpack"]
        beats = [dict(b, part_id="p1") for b in GOOD_ORDER]
        lesson_["videos"][0]["beats"] = beats
        return chapter, lesson_

    def test_the_examples_beats_become_a_story_piece_in_a_world_when_the_place_has_a_kit(self):
        chapter, lesson_ = self.lesson(example())
        summary = cd.run_canvas(chapter, lesson_, tcd.ECON, tcd.runner(self.tmp), self.tmp, workers=1)
        parts = summary["videos"][0]["parts"]
        self.assertEqual([(p["id"], p["mode"], p["story"], p["beats"]) for p in parts],
                         [("v1_s1a", "B", False, 1), ("v1_s1s", "C", True, 2), ("v1_s1b", "B", False, 1)])
        q = summary["quality"]
        self.assertEqual((q["story_parts"], q["story_parts_in_a_world"], q["missing_kits"]), (1, 1, []))
        self.assertEqual(q["parts_passed"], 3)
        self.assertIn("story (the real-world example)", Path(self.tmp, "CANVAS.md").read_text(encoding="utf-8"))

    def test_a_place_without_a_kit_stays_on_the_canvas_with_crowd_and_value_elements_and_is_logged(self):
        chapter, lesson_ = self.lesson(example(place="petrol pump", actors=["driver", "pump owner"], goods=["petrol"]))
        summary = cd.run_canvas(chapter, lesson_, tcd.ECON, tcd.runner(self.tmp), self.tmp, workers=1)
        story = next(p for p in summary["videos"][0]["parts"] if p["story"])
        self.assertEqual((story["id"], story["mode"], story["place"]), ("v1_s1s", "B", "petrol_pump"))
        self.assertEqual(summary["quality"]["missing_kits"], ["world kit for a petrol pump"])
        items = [{"item_id": "i1", "content_type": "definition", "content": "x", "real_world_example": example(place="petrol pump")}]
        mode = cd.mode_of(tcd.ECON, [{"beat_id": "b2", "say": "daam ₹100 se ₹105"}], items, story=True)
        self.assertEqual(mode, {"mode": "B", "place": "petrol_pump", "kit": "", "missing": "world kit for a petrol pump", "story": True})
        stub = {"id": "v1_s1s", "part_id": "p1", "beats": [{"beat_id": "b2", "say": "daam ₹100 se ₹105"}], "covers_item_ids": ["i1"],
                "on_screen_hints": [], "story": True}
        step = cd.part_step(tcd.ECON, stub, items, mode, rulebook=BOOK, menu=[("1f3ea", "shop")])
        self.assertIn("build the story on the canvas with crowd, value and icon elements", step.user)
        self.assertIn('"story": true', step.user)

    def test_a_part_without_an_example_or_without_the_numbers_is_not_split(self):
        full = {b["beat_id"]: b for b in GOOD_ORDER}
        stub = {"id": "v1_s1", "part_id": "p1", "beats": [{"beat_id": b["beat_id"], "say": b["say"]} for b in GOOD_ORDER],
                "covers_item_ids": ["i1"], "on_screen_hints": []}
        plain = [{"item_id": "i1", "content_type": "definition", "content": "x"}]
        self.assertEqual([(p["id"], p["story"]) for p in cd.story_split(stub, full, plain)], [("v1_s1", False)])
        with_example = [{"item_id": "i1", "content_type": "definition", "content": "x", "real_world_example": example()}]
        self.assertEqual([(p["id"], p["story"], len(p["beats"])) for p in cd.story_split(stub, full, with_example)],
                         [("v1_s1a", False, 1), ("v1_s1s", True, 2), ("v1_s1b", False, 1)])
        whole = dict(stub, beats=stub["beats"][1:3])
        self.assertEqual([(p["id"], p["story"]) for p in cd.story_split(whole, full, with_example)], [("v1_s1", True)])
        self.assertEqual(world.place_of("petrol pump par line lagi"), "petrol_pump")
        self.assertEqual(world.place_label("petrol_pump"), "petrol pump")


class FakeChain(unittest.TestCase):
    """The offline economics chapter: the fake maker fills the slot and speaks the example first, so Sections 1 and 2 pass
    on the first try, and the reports carry Navin's per-concept table."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        lines = [["Demand-pull inflation is a rise in prices because demand exceeds supply.",
                  "Money is anything accepted as a medium of exchange for goods and services.",
                  "The RBI controls the money supply through the repo rate."],
                 ["Inflation is measured by the consumer price index every month."]]
        self.pdf = Path(self.tmp.name, "money.pdf")
        self.pdf.write_bytes(t045.positioned_text_pdf([[(72, 720 - i * 20, t) for i, t in enumerate(page)] for page in lines]))

    def args(self, out):
        return ["--fake", "--section", "chain", "--source", str(self.pdf), "--out", str(Path(self.tmp.name, out)), "--workers", "1",
                "--course", "title=3. Money;subject=Indian Economy;learners=UPSC / State PCS aspirants;exam=UPSC / State PCS;language=Hinglish",
                "--max-inr", "100000"]

    def read(self, out, name):
        return json.loads(Path(self.tmp.name, out, name).read_text(encoding="utf-8"))

    def test_the_offline_economics_chapter_applies_every_concept_first_and_passes_first_try(self):
        code, _ = t045.run(self.args("econ"))
        self.assertEqual(code, 0)
        summary = self.read("econ", "SUMMARY.json")
        self.assertEqual(summary["status"], "ok")
        chapter = self.read("econ", "chapter_map.json")
        q = chapter["quality"]
        self.assertGreater(q["real_world_needed"], 0)
        self.assertEqual((q["real_world_filled"], q["real_world_ok"]), (q["real_world_needed"], q["real_world_needed"]))
        self.assertTrue(all(p["status"] == "passed" and p["rounds"] == 1 for p in chapter["pages"]))      # first try
        needing = [i for i in chapter["items"].values() if i.get("teachable") and TYPES.needs_real_world(ECON, i["content_type"])]
        self.assertTrue(all(i["unpack"]["real_world_example"]["place"] == "kirana shop" for i in needing))
        others = [i for i in chapter["items"].values() if i.get("teachable") and not TYPES.needs_real_world(ECON, i["content_type"])]
        self.assertTrue(all(i["unpack"]["real_world_example"]["place"] == "" for i in others))
        self.assertIn("## Real-world examples (S1-16", Path(self.tmp.name, "econ", "MAP.md").read_text(encoding="utf-8"))
        self.assertIn("real world (run it first", Path(self.tmp.name, "econ", "PAGES.md").read_text(encoding="utf-8"))
        lesson_ = self.read("econ", "lesson_plan.json")
        lq = lesson_["quality"]
        self.assertGreater(lq["real_world"]["items"], 0)
        self.assertEqual(lq["real_world"]["run_first"], lq["real_world"]["items"])
        self.assertEqual(lq["videos_passed"], lq["videos"])
        self.assertTrue(all(v["rounds"] == 1 for v in lesson_["videos"]))
        script = Path(self.tmp.name, "econ", "SCRIPT.md").read_text(encoding="utf-8")
        self.assertIn("## Real-world examples (S2-08", script)
        topic = next(v for v in lesson_["videos"] if v["kind"] == "topic" and v["real_world"])
        story_beats = [b for b in topic["beats"] if b["purpose"] == "story"]
        self.assertTrue(story_beats and all("₹50" in b["say"] and "12" in b["say"] for b in story_beats))

    def test_check_script_catches_a_term_named_before_its_example_on_the_real_card(self):
        code, _ = t045.run(self.args("econ2"))
        self.assertEqual(code, 0)
        chapter = self.read("econ2", "chapter_map.json")
        lesson_ = self.read("econ2", "lesson_plan.json")
        plan = lesson_["plan"]
        topic = next(v for v in lesson_["videos"] if v["kind"] == "topic" and v["real_world"])
        video = next(v for v in plan["videos"] if v["video_id"] == topic["video_id"])
        naksha = lesson.chapter_naksha(chapter)
        prefix = lesson.script_prefixes(COURSE, BOOK)[0]
        card = lesson.script_card(COURSE, chapter, naksha, plan, video, rulebook=BOOK, prefix=prefix)
        value = {"notes": {}, "title": topic["title"], "parts": topic["parts"],
                 "beats": [{k: b[k] for k in ("beat_id", "part_id", "step", "purpose", "say", "covers_item_ids", "answers", "on_screen", "basis")}
                           for b in topic["beats"]]}
        self.assertEqual([p for p in lesson.check_script(value, chapter, video, "Hinglish", card) if "S2-08" in p], [])
        row = topic["real_world"][0]
        story = next(i for i, b in enumerate(value["beats"]) if b["beat_id"] == row["example_beats"][0])
        term = chapter["items"][row["item_id"]]["unpack"]["terms"][0]["term"]
        explain = value["beats"][story + 1]
        explain["say"] = f"ये सामने क्या दिख रहा है? इसे {term} कहते हैं। " + explain["say"]
        value["beats"][story], value["beats"][story + 1] = explain, value["beats"][story]
        problems = [p for p in lesson.check_script(value, chapter, video, "Hinglish", card) if "S2-08" in p]
        self.assertEqual(len(problems), 1)
        self.assertIn(f"names '{term}' before its real-world example runs", problems[0])


if __name__ == "__main__":
    unittest.main()
