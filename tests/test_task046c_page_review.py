"""Seekh from the Money chapter's new-rule run (VM job t046c-money-understand-c, 27 October 2026): BIE's own S1-16 check passed
every one of the 102 economics concept items on the first try, yet 18 of 20 pages went back to the maker because the Codex checker
found more, and 24 of its 53 first-round blocking findings asked for a worked real-world example on timelines, classifications,
comparisons and fact lists, where rule S1-16 asks for none. Two more pages failed on one code slip the maker made while fixing the
checker's findings in the last allowed round, with no round left to mend it.

Now: in an economics chapter a blocking finding that wants a worked example on an item whose type does not carry the slot is
minor (the page passes when every blocking finding was such); the runner hands the maker's answer to a review that needs it; and
a first code slip after code-clean rounds counts as converging, so the step gets one more patch round. Every text below is test
input, never lesson content.
"""
from __future__ import annotations

import json
import sys
import types as pytypes
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain import content_types as ct, rulebook  # noqa: E402
from bie.brain.pages import Block, Page  # noqa: E402
from bie.brain.runner import SectionRunner, Step  # noqa: E402
from bie.brain.understanding import PAGE_REVIEW_HOW, Course, asks_for_example, page_review_problems, page_step  # noqa: E402

ECON = "economics_commerce_management"
BIO = "biology_medical"
TYPES = ct.load()
BOOK = rulebook.load()
COURSE = Course(title="3. Money", subject="Indian Economy", learners="UPSC / State PCS aspirants", exam="UPSC / State PCS",
                language="Hinglish", level="upsc_pcs")

# The checker's own first-round findings from the run (shortened): the item types are the maker's.
VALUE = {"items": [{"item_id": "i14", "content_type": "timeline"}, {"item_id": "i3", "content_type": "definition"},
                   {"item_id": "i25", "content_type": "classification"}, {"item_id": "i10", "content_type": "facts_numbers"},
                   {"item_id": "i31", "content_type": "cause_effect"}]}
ASK_TIMELINE = {"item_id": "i14", "what_is_missing": "The explanation correctly distinguishes commodity money from barter, but its "
                "real_world_example is empty. Show an explicitly illustrative market transaction.", "severity": "blocking"}
ASK_CLASS = {"item_id": "i25", "what_is_missing": "The two-axis distinction is conceptually sound but lacks a concrete worked example.",
             "severity": "blocking"}
ASK_FACTS = {"item_id": "i10", "what_is_missing": "The explanation of removing double coincidence of wants has no completed numerical "
             "example: real_world_example is empty.", "severity": "blocking"}
ASK_DEFINITION = {"item_id": "i3", "what_is_missing": "Legal tender is defined, but its real_world_example is empty. Add a settlement "
                  "example with a place, debtor and creditor and changing balances.", "severity": "blocking"}
LIST_NOT_OPENED = {"item_id": "i14", "what_is_missing": "UPI, NEFT and RTGS are listed but never opened; expand the acronyms and "
                   "explain each channel in accessible Hinglish.", "severity": "blocking"}
WRONG_MECHANISM = {"item_id": "i31", "problem": "The example's numbers move the wrong way: more buyers and a lower price.",
                   "fix": "Raise the price when buyers rise.", "severity": "blocking"}


def review(shallow=(), wrong=(), *, verdict="fail"):
    return {"verdict": verdict, "notes": {}, "missing": [], "wrong": list(wrong), "shallow": list(shallow), "checklist": []}


class TheExampleAskedWhereTheRuleDoesNotAsk(unittest.TestCase):
    def test_the_finding_is_recognised_by_its_words(self):
        for finding in (ASK_TIMELINE, ASK_CLASS, ASK_FACTS, ASK_DEFINITION):
            self.assertTrue(asks_for_example(finding), finding["what_is_missing"][:40])
        self.assertFalse(asks_for_example(LIST_NOT_OPENED))
        self.assertFalse(asks_for_example({"problem": "RBI was set up in 1935, not 1934."}))

    def test_minor_on_a_timeline_blocking_on_a_definition(self):
        problems = page_review_problems(review(shallow=[ASK_TIMELINE, ASK_DEFINITION]), VALUE, family=ECON, types=TYPES)
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0].startswith("shallow i3: "))

    def test_a_page_whose_only_findings_were_such_passes_and_other_findings_still_block(self):
        self.assertEqual(page_review_problems(review(shallow=[ASK_TIMELINE, ASK_CLASS, ASK_FACTS]), VALUE, family=ECON, types=TYPES), [])
        kept = page_review_problems(review(shallow=[ASK_TIMELINE, LIST_NOT_OPENED], wrong=[WRONG_MECHANISM]), VALUE, family=ECON,
                                    types=TYPES)
        self.assertEqual(len(kept), 2)
        self.assertTrue(any(p.startswith("shallow i14: UPI, NEFT") for p in kept))
        self.assertTrue(any(p.startswith("wrong in i31: ") for p in kept))

    def test_outside_economics_and_without_a_family_nothing_changes(self):
        bio = page_review_problems(review(shallow=[ASK_TIMELINE]), VALUE, family=BIO, types=TYPES)
        self.assertEqual(len(bio), 1)
        self.assertEqual(len(page_review_problems(review(shallow=[ASK_TIMELINE]), VALUE, types=TYPES)), 1)

    def test_a_fail_naming_nothing_and_a_pass_behave_as_before(self):
        back = page_review_problems(review(), VALUE, family=ECON, types=TYPES)
        self.assertEqual(len(back), 1)
        self.assertIn("named no blocking finding", back[0])
        self.assertEqual(page_review_problems(review(verdict="pass"), VALUE, family=ECON, types=TYPES), [])
        self.assertEqual(page_review_problems(review(verdict="pass"), {}, family=ECON, types=TYPES), [])

    def test_the_page_step_reviews_with_the_items_in_hand_and_the_checker_is_told(self):
        page = Page(1, (Block("p0001-b0001", "Money is anything generally accepted in payment.", (0, 0, 1, 1)),))
        step = page_step(COURSE, page, page_count=1, rulebook=BOOK)
        self.assertEqual(step.review_problems(review(shallow=[ASK_TIMELINE]), VALUE), [])
        self.assertEqual(len(step.review_problems(review(shallow=[ASK_DEFINITION]), VALUE)), 1)
        self.assertIn("is\n  correct, not a finding", PAGE_REVIEW_HOW)
        system = step.review_system if isinstance(step.review_system, str) else str(step.review_system)
        self.assertIn("counts such a finding as minor", system)


class Stub:
    def __init__(self, answers, reviews=()):
        self.answers, self.reviews, self.requests = list(answers), list(reviews), []

    def complete(self, route, request, prompt_version=None):
        self.requests.append((route, request))
        content = self.reviews.pop(0) if route == "rev" else self.answers.pop(0)
        return pytypes.SimpleNamespace(content=content, provenance={"via": "fake"}, model="stub", provider=route,
                                       usage={"input_tokens": 1, "output_tokens": 1})


def step(review_problems, **extra):
    return Step(section="understand", unit="page-001", instructions_version="v", system="S", user="U", schema={"full": 1},
                check=lambda value: [] if value["ok"] else [f"item i1: block_ids are not blocks of this page ({value['n']})"],
                review_system="R", review_user=lambda value: "review this", review_schema={}, review_problems=review_problems,
                patch_schema={"patch": 1}, apply_patch=lambda old, patch: dict(old, **patch), **extra)


FAIL = {"verdict": "fail", "problems": [{"problem": "too shallow", "severity": "blocking"}]}
PASS = {"verdict": "pass", "problems": []}
one_arg = lambda review: [f["problem"] for f in review.get("problems", [])]  # noqa: E731


class TheRunner(unittest.TestCase):
    def runner(self, stub):
        return SectionRunner(stub, maker="maker", reviewer="rev", rulebook=BOOK)

    def test_a_two_argument_review_gets_the_makers_answer(self):
        seen = []

        def two_args(review, value):
            seen.append(value["n"])
            return one_arg(review)

        stub = Stub(answers=[{"ok": True, "n": 7, "notes": None}], reviews=[PASS])
        result = self.runner(stub).run(step(two_args))
        self.assertEqual((result.status, seen), ("passed", [7]))
        stub = Stub(answers=[{"ok": True, "n": 1, "notes": None}], reviews=[PASS])
        self.assertEqual(self.runner(stub).run(step(one_arg)).status, "passed")      # the one-argument form still works

    def test_a_slip_in_the_last_round_gets_one_more_patch_round(self):
        stub = Stub(answers=[{"ok": True, "n": 1, "notes": None}, {"ok": True, "n": 2}, {"ok": False, "n": 3}, {"ok": True, "n": 4}],
                    reviews=[FAIL, FAIL, PASS])
        result = self.runner(stub).run(step(one_arg, max_rounds=3))
        self.assertEqual(result.status, "passed")
        self.assertEqual([r["round"] for r in result.rounds], [1, 2, 3, 4])
        self.assertTrue(result.rounds[3].get("extra_round"))
        self.assertEqual(result.rounds[2]["code_problems"], ["[code] item i1: block_ids are not blocks of this page (3)"])
        self.assertEqual([route for route, _ in stub.requests], ["maker", "rev", "maker", "rev", "maker", "maker", "rev"])

    def test_code_problems_that_do_not_shrink_still_end_at_max_rounds(self):
        stub = Stub(answers=[{"ok": False, "n": 1, "notes": None}, {"ok": False, "n": 2}, {"ok": False, "n": 3}], reviews=[])
        result = self.runner(stub).run(step(one_arg, max_rounds=3))
        self.assertEqual(result.status, "failed")
        self.assertEqual([r["round"] for r in result.rounds], [1, 2, 3])
        self.assertEqual(stub.requests[-1][0], "maker")

    def test_a_slip_in_the_first_round_is_not_a_slip(self):
        stub = Stub(answers=[{"ok": False, "n": 1, "notes": None}], reviews=[])
        result = self.runner(stub).run(step(one_arg, max_rounds=1))
        self.assertEqual(result.status, "failed")
        self.assertEqual([r["round"] for r in result.rounds], [1])


if __name__ == "__main__":
    unittest.main()
