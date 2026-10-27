"""Seekh from the Money chapter's baseline run (VM job t046c-money-understand-b, 27 October 2026): the chapter map failed after
three rounds although every code check passed every round, because the reviewer kept finding new wording to improve inside
core_explanation, notes and exam_focus (10 of its 12 blocking findings), two-line summaries no learner hears. The map is
structure; wording findings on its summary fields are kept in the record as minor and never fail the map; structural
findings (items, relations, prerequisites, references, question links, teaching order) still block.

The `where` strings below are the reviewer's own placements from that run's record: test input, never lesson content.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain import rulebook  # noqa: E402
from bie.brain.understanding import (CONNECT_REVIEW_HOW, Course, connect_review_problems, connect_step, structural_finding,  # noqa: E402
                                     wording_findings)

BOOK = rulebook.load()
COURSE = Course(title="3. Money", subject="Indian Economy", learners="UPSC / State PCS aspirants", exam="UPSC / State PCS",
                language="Hinglish", level="upsc_pcs")

# The baseline map's three reviewer rounds (verdict fail each time; the code found 0 problems each time).
ROUND_0 = ["c15.core_explanation; notes.uncertain; exam_focus[c15]", "c28.core_explanation", "c07.core_explanation",
           "c09.core_explanation", "prerequisites_to_teach", "c01.core_explanation; c02.core_explanation"]
ROUND_1 = ["concepts[c13].core_explanation; p007-i10", "concepts[c04].core_explanation; p002-i8–p002-i11",
           "concepts[c17].core_explanation; p009-i15–p009-i22"]
ROUND_2 = ["c37.core_explanation; p018-i4", "c35.core_explanation; notes.uncertain cryptocurrency-origin entry",
           "relations: c32 depends_on c30"]
MINOR = ["relations involving c03", "c19.core_explanation"]


def review(wheres, *, verdict="fail", minor=()):
    problems = [{"where": w, "problem": f"problem at {w}", "fix": f"fix at {w}", "severity": "blocking"} for w in wheres]
    problems += [{"where": w, "problem": "could be clearer", "fix": "one line", "severity": "minor"} for w in minor]
    return {"verdict": verdict, "problems": problems, "notes": {}, "checklist": []}


class WhereIsTheFinding(unittest.TestCase):
    def test_summary_wording_is_not_structure(self):
        for where in ROUND_0[:4] + ROUND_0[5:] + ROUND_1 + ROUND_2[:2]:
            self.assertFalse(structural_finding(where), where)

    def test_items_relations_prerequisites_and_order_are_structure(self):
        for where in ("prerequisites_to_teach", "relations: c32 depends_on c30", "concepts[c03].item_ids", "teaching_order",
                      "cross_references[2]", "question_links", "p004-i7 left out of every concept"):
            self.assertTrue(structural_finding(where), where)

    def test_a_finding_naming_both_is_structure_and_an_unplaced_one_blocks(self):
        self.assertTrue(structural_finding("c07.core_explanation; relations c07 -> c08"))
        self.assertTrue(structural_finding(""))
        self.assertTrue(structural_finding("   "))
        self.assertTrue(structural_finding("the whole map"))


class TheMapReview(unittest.TestCase):
    def test_the_baseline_rounds_replayed_pass_at_round_1(self):
        first = connect_review_problems(review(ROUND_0, minor=[MINOR[0]]))
        self.assertEqual(len(first), 1)
        self.assertTrue(first[0].startswith("prerequisites_to_teach: "))
        self.assertEqual(connect_review_problems(review(ROUND_1)), [])             # the map would have passed here
        third = connect_review_problems(review(ROUND_2, minor=[MINOR[1]]))
        self.assertEqual(len(third), 1)
        self.assertTrue(third[0].startswith("relations: c32 depends_on c30: "))

    def test_wording_findings_stay_in_the_record(self):
        kept = wording_findings(review(ROUND_0))
        self.assertEqual([f["where"] for f in kept], ROUND_0[:4] + ROUND_0[5:])
        self.assertEqual(wording_findings(review(ROUND_1)), review(ROUND_1)["problems"])
        self.assertEqual(wording_findings(review([], verdict="pass")), [])

    def test_a_fail_naming_nothing_still_goes_back_once(self):
        problems = connect_review_problems(review([]))
        self.assertEqual(len(problems), 1)
        self.assertIn("named no blocking finding", problems[0])
        minor_only = connect_review_problems(review([], minor=["c19.core_explanation"]))
        self.assertIn("named no blocking finding", minor_only[0])                  # fail with minor only: back once, as every section

    def test_pass_and_minor_findings_never_block(self):
        self.assertEqual(connect_review_problems(review([], verdict="pass", minor=MINOR)), [])
        self.assertEqual(connect_review_problems(review([], verdict="pass")), [])

    def test_the_connect_step_reviews_structure_and_says_so(self):
        items = {"p001-i1": {"item_id": "p001-i1", "page": 1, "kind": "paragraph", "content_type": "definition", "teachable": True,
                             "exam_importance": "high", "content": "Money is anything generally accepted in payment.",
                             "block_ids": ["b1"], "prerequisites": []},
                 "p001-i2": {"item_id": "p001-i2", "page": 1, "kind": "paragraph", "content_type": "process", "teachable": True,
                             "exam_importance": "medium", "content": "Barter needs a double coincidence of wants.",
                             "block_ids": ["b2"], "prerequisites": []}}
        step = connect_step(COURSE, items, rulebook=BOOK)
        self.assertIs(step.review_problems, connect_review_problems)
        system = step.review_system if isinstance(step.review_system, str) else str(step.review_system)
        self.assertIn("core_explanation is a two-line summary", system)
        self.assertIn("counts only structural findings as blocking", CONNECT_REVIEW_HOW)


if __name__ == "__main__":
    unittest.main()
