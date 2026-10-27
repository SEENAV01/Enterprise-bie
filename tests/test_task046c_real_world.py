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


def item(iid, block_ids, kind, *asks):
    """A teachable item as Section 1 writes it (the same shape as tests/test_task045_cards.item, without that file's pypdf)."""
    qa = [{"depth": 1 if n == 0 else 2, "ask": ask, "question": f"{ask}?", "answer": f"an answer for {ask}", "basis": "book"}
          for n, ask in enumerate(asks)]
    return {"item_id": iid, "kind": "paragraph", "parent_item_id": "", "source": "text", "block_ids": list(block_ids),
            "where_on_page": "top", "content": "Demand-pull inflation is a rise in prices.", "content_type": kind, "type_note": "",
            "teachable": True, "teacher_understanding": qa, "prerequisites": [], "exam_importance": "medium", "exam_note": "",
            "tests_item_ids": [], "unpack": {}}


def econ_item(iid="i1", kind="definition", ex=None):
    item_ = item(iid, ["p0001-b0001"], kind, "what", "evidence", "why")
    item_["unpack"] = {"terms": [{"term": "demand-pull inflation", "plain_meaning": "माँग बढ़ने से दाम बढ़ना", "everyday_image": "मंडी"}],
                       "why_chain": [{"step": "लोग ज़्यादा, माल उतना ही", "basis": "book"}], "example_or_place": "", "consequence": "",
                       "visual_verb": "", "level_extra": "", "real_world_example": ex if ex is not None else example()}
    return item_


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
        for name in ("vision-2026-10-21@2026-10-21.14", "content_types@2026-10-27.1", "teacher_examples@2026-10-27.1", "simple_hindi@2026-10-27.2"):
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
        chapter = {"course": {"title": "3. Money", "subject": "Indian Economy", "learners": "UPSC", "exam": "UPSC", "language": "Hinglish"},
                   "items": {"p001-i1": dict(econ_item("p001-i1"), page=1),
                             "p001-i2": dict(econ_item("p001-i2", ex=dict(soul.EMPTY_REAL_WORLD)), page=1)},
                   "map": {"concepts": [{"concept_id": "c1", "name": "Inflation", "item_ids": ["p001-i1", "p001-i2"]}]},
                   "pages": [{"page": 1, "status": "passed", "rounds": 1, "summary": "", "last_problems": [], "cost_usd": 0.0,
                              "item_ids": ["p001-i1", "p001-i2"]}], "cost_usd": 0.0, "map_status": "passed"}
        rows = understanding.real_world_rows(chapter)
        self.assertEqual([(r["item_id"], r["concept"], r["ok"], r["first_try"]) for r in rows],
                         [("p001-i1", "Inflation", True, True), ("p001-i2", "Inflation", False, True)])   # first try is the page's
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


class SeekhFromTheFirstMoneyRun(unittest.TestCase):
    """VM job t046c-money-understand (27 October 2026, old rules): page 2 lost a round to 'पदार्थ → substance' although the Money
    chapter never says 'substance', and the stopped page's record kept only 300 characters of Google's 429, hiding the quota id."""

    def test_textbook_hindi_counts_only_for_the_books_own_terms(self):
        from bie.brain import hinglish
        money = hinglish.english_terms("Commodity money is a form of money in which the item used as money has intrinsic value.")
        tissue = hinglish.english_terms("Cells of a tissue are held in a substance called the matrix.")
        self.assertEqual(hinglish.technical_words("इस पदार्थ का अपना मूल्य है", book_terms=money), [])
        self.assertEqual(hinglish.technical_words("इस पदार्थ का अपना मूल्य है", book_terms=tissue), [("पदार्थ", "substance")])
        self.assertEqual(hinglish.technical_words("इस पदार्थ का अपना मूल्य है"), [("पदार्थ", "substance")])        # no book: as before
        self.assertEqual(hinglish.technical_words("कोशिका का पदार्थ", book_terms=tissue), [("कोशिका", "cell"), ("पदार्थ", "substance")])
        self.assertEqual(hinglish.term_stem("tissues"), "tissue")
        self.assertEqual(hinglish.term_stem("bodies"), "body")
        item = econ_item()
        item["unpack"]["terms"][0]["plain_meaning"] = "ऐसा पदार्थ जिसका अपना मूल्य हो"
        self.assertEqual([p for p in soul.unpack_problems(item, book_terms=money) if "textbook" in p], [])
        self.assertEqual(len([p for p in soul.unpack_problems(item, book_terms=tissue) if "textbook" in p]), 1)
        page = Page(1, (Block("p0001-b0001", "Commodity money has intrinsic value.", (0, 0, 1, 1)),))
        value = {"notes": {}, "page_summary": "", "boilerplate_block_ids": [], "text_image_disagreements": [], "items": [item]}
        self.assertEqual([p for p in understanding.check_page(value, page, family=ECON) if "textbook" in p], [])
        beat_ = beat("b1", "यह ऐसा पदार्थ है जिसका अपना मूल्य है, जैसे सोना।")
        self.assertEqual([p for p in lesson.spoken_problems([beat_], "Hinglish", money) if "textbook" in p], [])
        self.assertEqual(len([p for p in lesson.spoken_problems([beat_], "Hinglish", tissue) if "textbook" in p]), 1)

    def test_the_record_keeps_the_providers_whole_error(self):
        import inspect
        from bie.brain import runner
        source = inspect.getsource(runner)
        self.assertNotIn("str(exc)[:300]", source)
        self.assertEqual(source.count("str(exc)[:1500]"), 2)


if __name__ == "__main__":
    unittest.main()
