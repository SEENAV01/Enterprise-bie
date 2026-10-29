"""Task 046 Part C · work C, first piece: the five Money scripts the lesson resume -d could not pass (v2, v4, v10, v11, v12)
are now caught by BIE's code before the reviewer sees them.

Offline, on small scripts: W-01 refuses a sentence that says what the source lacks ("dates नहीं हैं", "data not given", a
caption that "supplies no source") in the narration and in the on-screen text; S2-10 asks a competitive-exam teaching beat
for its dated source when it teaches about an institution from outside the book (a story, a hook, a school lesson and a beat
whose book line names the institution need none); S2-08 refuses a teaching beat of the same concept that names the term before
the example runs, with the acronym of the naming sentence counted as the term; the rulebooks, the regression registry, the
script schema and the fake maker carry the change.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain import content_types as ct  # noqa: E402
from bie.brain import fake, lesson, regression, rulebook, soul  # noqa: E402


def _beat(bid, say, *, part="c01.1", purpose="explain", basis="mixed", covers=(), on_screen="", source=""):
    return {"beat_id": bid, "part_id": part, "step": 1, "purpose": purpose, "say": say, "covers_item_ids": list(covers), "answers": [],
            "on_screen": on_screen, "basis": basis, "source": source}


class SourceLacks(unittest.TestCase):
    def test_saying_what_the_source_lacks_is_refused_in_three_languages(self):
        beats = [_beat("b24", "Evolution of Money का पहला पड़ाव barter है: wheat के बदले सीधा कपड़ा; dates नहीं हैं।"),
                 _beat("b56", "Dates नहीं दी गईं। Salt खाने में काम आता है।"),
                 _beat("b3", "Is page par exact figures nahi diye gaye, lekin trend saaf hai."),
                 _beat("b4", "The exact shares are not given, so take the order as qualitative."),
                 _beat("b5", "कल 2 खरीदार आए, आज 12: दाम ₹50 से बढ़कर ₹65 हो गया।")]            # the story's own numbers: fine
        problems = soul.wording_problems(beats)
        self.assertEqual([p.split(":")[0] for p in problems], ["beat b24", "beat b56", "beat b3", "beat b4"])
        self.assertTrue(all(p.endswith("(W-01)") for p in problems))
        self.assertIn("'dates नहीं हैं'", problems[0])

    def test_the_on_screen_text_is_read_too(self):
        on = ("Source-evidence annotations, not narration: USD caption supplies no numerical shares or data source. "
              "EUR caption ends at 'second-most'; ranking measure unspecified.")
        beats = [_beat("b30", "इन descriptions से exact market shares मत निकालिए।", on_screen=on),
                 _beat("b28", "CRR का मतलब समझिए।", on_screen="Bankers' Deposits with RBI includes CRR; no numerical ratio supplied."),
                 _beat("b7", "Barter में wheat के बदले कपड़ा।", on_screen="Wheat ↔ cloth: both must want the other's goods.")]
        problems = soul.wording_problems(beats)
        self.assertEqual([p.split(":")[0] for p in problems], ["beat b30", "beat b28"])
        self.assertIn("on_screen", problems[0])
        self.assertIn("never what the source gives or lacks (W-01)", problems[0])


ITEMS = {"p011-i10": {"item_id": "p011-i10", "content": "Payments can be made through cheques, UPI, debit cards, NEFT, RTGS.", "teachable": True},
         "p013-i3": {"item_id": "p013-i3", "content": "Rahul pays the merchant through the app.", "teachable": True}}


class DatedSource(unittest.TestCase):
    def test_a_competitive_exam_teaching_beat_about_an_outside_institution_names_its_dated_source(self):
        beats = [_beat("b20", "दुकान का QR app से scan करो: UPI deposit तुरंत दूसरे account में पहुँचाता है।", covers=["p011-i10"]),
                 _beat("b21", "Rent के लिए NEFT instruction दो: settlement batches में होता है।", basis="outside", covers=["p011-i10"]),
                 _beat("b22", "RBI पीछे settlement framework की oversight करता है।", covers=["p013-i3"]),
                 _beat("b23", "RBI पीछे settlement framework की oversight करता है।", covers=["p013-i3"], source="RBI, Payment and Settlement Systems Act, 2007"),
                 _beat("b24", "RBI पीछे settlement framework की oversight करता है।", covers=["p013-i3"], source="RBI website"),
                 _beat("b25", "Rahul app से ₹100 का राशन चुकाता है; receipt ₹0 से ₹100।", purpose="example", basis="outside", covers=["p013-i3"]),
                 _beat("b26", "UPI से पैसा कैसे जाता है?", purpose="hook", basis="outside"),
                 _beat("b27", "NPCI दोनों banks को जोड़ता है।", basis="book", covers=["p013-i3"])]
        problems = soul.dated_source_problems(beats, ITEMS, level="upsc_pcs")
        self.assertEqual([p.split(":")[0] for p in problems], ["beat b21", "beat b22", "beat b24"])
        self.assertIn("teaches about NEFT from outside the book", problems[0])        # outside basis: the institution it teaches about
        self.assertIn("names RBI that its book lines do not", problems[1])             # mixed: UPI in b20 is in its book line, RBI is not
        self.assertIn("carries no dated source", problems[2])                           # "RBI website" has no year
        self.assertTrue(all(p.endswith("(S2-10)") for p in problems))
        self.assertEqual(soul.dated_source_problems(beats, ITEMS, level="school"), [])   # a school lesson is not examined on sources
        self.assertEqual(soul.outside_facts(beats[0], ITEMS), [])
        self.assertEqual(soul.outside_facts(beats[2], ITEMS), ["RBI"])

    def test_the_script_check_runs_it_for_the_chapters_level(self):
        text = (ROOT / "bie/brain/lesson.py").read_text(encoding="utf-8")
        self.assertIn('soul.dated_source_problems(beats, chapter["items"], level=str(chapter.get("level") or ""))', text)
        self.assertIn('"source": S,', text)
        self.assertEqual(lesson.SCRIPT_VERSION, "lesson-script/6")
        self.assertIn("source", lesson.BEAT_SCHEMA["required"])


UNPACK = {"terms": [{"term": "interoperable"}, {"term": "Delhi Sultanate"}, {"term": "Token Currency"}],
          "real_world_example": {"place": "kirana shop", "actors": ["household"], "goods": ["electricity bill"],
                                 "numbers": [{"what": "due", "before": "₹600", "after": "₹0"}],
                                 "steps": [{"step": "pay", "mechanism_link": "a"}, {"step": "settle", "mechanism_link": "b"}],
                                 "term_after": "This common bill-payment arrangement is Bharat Bill Payment System, or BBPS; token currency is another story.",
                                 "real_life_link": "electricity bills"}}
CHAPTER_ITEMS = {"p015-i4": {"item_id": "p015-i4", "content_type": "definition", "teachable": True, "unpack": UNPACK},
                 "p015-i5": {"item_id": "p015-i5", "content_type": "definition", "teachable": True, "unpack": {"terms": [{"term": "AePS"}]}}}
PARTS = [{"part_id": "c29.1", "type": "definition", "item_ids": ["p015-i5"]}, {"part_id": "c29.4", "type": "definition", "item_ids": ["p015-i4"]}]


class ExampleFirstAcrossTheConcept(unittest.TestCase):
    def setUp(self):
        self.types = ct.load()
        self.family = "economics_commerce_management"

    def order(self, beats):
        return soul.example_order_problems(beats, CHAPTER_ITEMS, PARTS, family=self.family, types=self.types)

    def test_a_sister_part_naming_the_term_before_the_example_is_refused_and_a_hook_may_ask(self):
        beats = [_beat("b1", "BBPS से bill कैसे भरते हैं?", part="", purpose="hook", covers=[]),
                 _beat("b33", "AePS और BBPS दोनों को NPCI manage करता है।", part="c29.1", covers=["p015-i5"]),
                 _beat("b44", "Household ₹600 का electricity bill भरता है; due ₹600 से ₹0।", part="c29.4", purpose="example", covers=["p015-i4"]),
                 _beat("b45", "यह Bharat Bill Payment System, BBPS है: single interoperable platform।", part="c29.4", covers=["p015-i4"])]
        problems = self.order(beats)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("beat b33: names 'BBPS' before its real-world example runs (beat b44)", problems[0])
        self.assertEqual(self.order([beats[0], beats[2], beats[3], beats[1]]), [])        # after the example: fine
        other = dict(beats[1], part_id="c28.1")                                               # another concept's beat: not this item's naming
        self.assertEqual(self.order([beats[0], other, beats[2], beats[3]]), [])

    def test_only_the_terms_the_naming_sentence_names_are_kept_for_after_the_example(self):
        self.assertEqual(soul.naming_terms(UNPACK, UNPACK["real_world_example"]), ["Token Currency", "BBPS"])
        no_sentence = {"terms": UNPACK["terms"], "real_world_example": {"term_after": ""}}
        self.assertEqual(soul.naming_terms(no_sentence, no_sentence["real_world_example"]), ["interoperable", "Delhi Sultanate", "Token Currency"])
        self.assertEqual(soul.ACRONYM.findall("This illustrates the UPI transaction route; AePS and BBPS too."), ["UPI", "AePS", "BBPS"])


class RulebookAndFake(unittest.TestCase):
    def test_the_rulebooks_carry_the_change(self):
        vision = json.loads((ROOT / "bie/brain/rulebook/vision-2026-10-21.json").read_text(encoding="utf-8"))
        self.assertEqual(vision["version"], "2026-10-21.16")
        rules = {r["id"]: r for r in vision["rules"]}
        self.assertIn("S2-10", rules)
        self.assertIn("dated source", rules["S2-10"]["rule"])
        self.assertIn("teaching beat of the same concept", rules["S2-08"]["rule"])
        self.assertTrue(vision["changes"][-1].startswith("2026-10-21.16"))
        grammar = json.loads((ROOT / "bie/brain/rulebook/visual_grammar.json").read_text(encoding="utf-8"))
        self.assertEqual(grammar["version"], "2026-10-29.1")
        self.assertTrue(grammar["changes"][-1].startswith("2026-10-29.1"))
        book = rulebook.load()
        self.assertIn("vision-2026-10-21@2026-10-21.16", book.version)
        self.assertIn("visual_grammar@2026-10-29.1", book.version)
        self.assertIn("S2-10", {r.id for r in book.for_section("lesson")})

    def test_the_regression_registry_explains_the_new_findings_for_earlier_passed_scripts(self):
        old = {"rulebook": "visual_grammar@2026-10-28.1+vision-2026-10-21@2026-10-21.15"}
        self.assertEqual(regression._changed(old, "beat b7: x (S2-10)")["rule"], "S2-10")
        self.assertEqual(regression._changed(old, "beat b33: names 'BBPS' before its real-world example runs (beat b44); the story with its numbers comes first, the name after (S2-08)")["rulebook"],
                         f"{regression.VISION}@2026-10-21.16")
        self.assertEqual(regression._changed(old, "beat b7: x (W-01)")["rulebook"], "visual_grammar@2026-10-29.1")
        new = {"rulebook": "visual_grammar@2026-10-29.1+vision-2026-10-21@2026-10-21.16"}
        for problem in ("beat b7: x (S2-10)", "beat b7: x (W-01)", "beat b7: x (S2-08)"):
            self.assertIsNone(regression._changed(new, problem))

    def test_the_fake_maker_writes_the_source_field(self):
        text = (ROOT / "bie/brain/fake.py").read_text(encoding="utf-8")
        self.assertIn('b.setdefault("source", "")', text)
        self.assertIn('"basis": "book", "source": ""', text)
        self.assertIn("source = for a competitive-exam learner", (ROOT / "bie/brain/lesson.py").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
