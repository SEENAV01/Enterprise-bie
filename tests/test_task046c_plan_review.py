"""Seekh from the Money chapter's first lesson run (VM job t046c-money-lesson, 27 October 2026): the lesson plan passed every code
check in every round and failed after three rounds because the Codex checker judged the plan as if it were the lesson: all 20 of its
blocking findings asked the plan for the teaching itself (beats, complete questions and answers, worked examples, the example-first
order, spoken narration), which the next step writes one script per video and reviews there. The plan reviewer's checklist carried
every lesson rule, the script rules included.

Now the plan reviewer gets a plan prefix (what a plan is, what the scripts carry) and the plan's own checklist (G-04, S2-01, S2-03),
and BIE's code counts only structural findings as blocking: a concept in no video or before its prerequisite, a grouping that splits a
family or packs too much into a video's minutes, a prerequisite list the chapter does not need. The texts below are the checker's own
placements from that run, shortened: test input, never lesson content.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain import rulebook  # noqa: E402
from bie.brain.lesson import (PLAN_REVIEW_HOW, PLAN_RULES, plan_checklist_text, plan_review_problems, plan_step,  # noqa: E402
                              plan_structural_finding)
from bie.brain.understanding import Course  # noqa: E402

BOOK = rulebook.load()
COURSE = Course(title="3. Money", subject="Indian Economy", learners="UPSC / State PCS aspirants", exam="UPSC / State PCS",
                language="Hinglish", level="upsc_pcs")

# The Codex checker's 20 blocking findings on the Money plan (where · problem, shortened), rounds 0, 1 and 2.
MONEY_PLAN_FINDINGS = [
    ("v1–v15: goals and story_or_analogy fields", "The videos name teaching intentions but do not actually teach the concepts."),
    ("v0: prerequisites_taught, goal and story_or_analogy", "All 25 prerequisites are declared taught, but only a few example scenes "
     "are named. There are no actual explanations of settlement or redemption."),
    ("v16–v17: practice coverage", "The plan promises to preserve and solve every printed statement and option while deferring their "
     "wording to later verification. No complete question, option elimination or answer appears."),
    ("v1–v15: content-type teaching patterns and economics examples", "The required teaching patterns are mostly named rather than "
     "executed. Classification members and their common slots are absent."),
    ("v1–v17: learner-facing narration", "Hooks are natural Hinglish, but most remaining text is production direction rather than "
     "complete spoken teaching. There is also no beat structure."),
    ("v1–v17; notes.decisions concerning planned coverage", "Goals and future-tense promises replace the teachable explanations."),
    ("v2, v4, v6–v7, v9–v14", "Important exam content is deferred to unspecified source-listed material."),
    ("v3–v5, v11, v13, v15", "Required process and causal patterns are incomplete. Tughlaq's actual sequence is deferred, redemption "
     "is not run through, UPI routing is not demonstrated step by step."),
    ("v16–v17", "The five practice concepts have time allocations but no complete questions, alternatives or final solutions."),
    ("v0", "The prerequisite video compresses 25 ideas into short definition fragments. Several do not receive the claimed "
     "explanation–example pair."),
    ("v4–v7, v10, v12, v14–v15", "The example-first economics rule is not consistently implemented."),
    ("v2, v4–v7, v9, v11–v17", "Numerous explanations are left to source material, but the actual teaching is absent."),
    ("v2–v17 story_or_analogy fields", "If these fields are intended as learner-facing narration, phrases such as 'source-listed' "
     "point to the source instead of teaching."),
    ("v1–v15; videos[].goal and story_or_analogy", "Most videos supply short illustrative paragraphs and intentions, not complete "
     "teaching beats."),
    ("v1–v2, v4, v6–v7, v9–v14", "Explicitly missing examinable content includes good-money characteristics and commodity–region "
     "matches."),
    ("v3–v5, v11, v13, v15", "Mechanisms stop at introductory sketches: Tughlaq's actual sequence and consequences, the gold-to-fiat "
     "transition."),
    ("v16–v17 / c37–c41", "Practice videos contain no original questions, alternatives, answer combinations, keys or solutions."),
    ("v0 / prerequisites_taught and story_or_analogy", "The claim that all 25 prerequisites are taught exceeds the explanation "
     "provided."),
    ("v2, v6–v7, v9, v12–v15", "Required content-type patterns are largely absent: no complete classification trees."),
    ("v1, v4–v6, v9–v12, v14–v15", "The example-first economics rule is not consistently implemented. Several terms are introduced as "
     "labels without first running a concrete numerical situation."),
]
STRUCTURAL = [
    ("v5", "v5 packs 8 concepts (c12, c13, c14, c15, c16, c33, c35, c17) into a 16-minute video, combining the entire muscle family "
     "and neuron impulse transmission."),                                                   # the tissue plan's Gemini finding
    ("c37", "Concept c37 (MDR) is in no video."),
    ("v3: concept_ids", "v3 teaches c05 before its prerequisite c02, which comes in v4."),
    ("v0: prerequisites_taught", "The list names 'settlement', which the chapter does not need (S2-03)."),
    ("v9", "The two members of the payment-systems family are split across v9 and v12."),
]


def finding(where, problem, severity="blocking"):
    return {"where": where, "problem": problem, "fix": "see the problem", "severity": severity}


def review(findings, *, verdict="fail"):
    return {"verdict": verdict, "notes": {}, "problems": list(findings), "checklist": []}


def small_chapter():
    def item(iid, page, kind_type, content, kind="paragraph", teachable=True):
        qa = [{"depth": 1, "ask": "what", "question": "Question?", "answer": "Answer here.", "basis": "book"}] if teachable else []
        return {"item_id": iid, "page": page, "kind": kind, "parent_item_id": "", "source": "text", "block_ids": [f"p{page:04d}-b0001"],
                "where_on_page": "", "content": content, "content_type": kind_type, "type_note": "", "teachable": teachable,
                "teacher_understanding": qa, "prerequisites": [], "exam_importance": "high", "exam_note": "", "tests_item_ids": [],
                "unpack": {"terms": [], "why_chain": [], "example_or_place": "", "consequence": "", "visual_verb": "", "level_extra": ""}
                if teachable else None}
    items = {"p001-i1": item("p001-i1", 1, "definition", "Money is anything generally accepted in payment."),
             "p001-i2": item("p001-i2", 1, "process", "Barter needs a double coincidence of wants."),
             "p002-i1": item("p002-i1", 2, "cause_effect", "More buyers and the same sugar raise its price.")}
    concepts = [{"concept_id": "c1", "name": "Money", "item_ids": ["p001-i1"], "content_type": "definition", "core_explanation": "x"},
                {"concept_id": "c2", "name": "Barter", "item_ids": ["p001-i2"], "content_type": "process", "core_explanation": "x"},
                {"concept_id": "c3", "name": "Demand-pull inflation", "item_ids": ["p002-i1"], "content_type": "cause_effect",
                 "core_explanation": "x"}]
    return {"schema": "bie.brain.chapter-map/2", "course": {"title": "3. Money", "subject": "Indian Economy", "learners": "UPSC",
                                                           "exam": "UPSC", "language": "Hinglish"},
            "source_sha256": "a" * 64, "page_count": 2, "rulebook_version": BOOK.version, "pages": [{"page": 1}, {"page": 2}],
            "items": items,
            "map": {"chapter_summary": "Money.", "concepts": concepts,
                    "relations": [{"from_concept": "c1", "relation": "depends_on", "to_concept": "c2", "note": ""}],
                    "prerequisites_to_teach": [{"name": "Price", "why_needed": "x", "needed_for": ["c3"], "basis": "outside"}],
                    "cross_references": [], "question_links": [], "teaching_order": ["c2", "c1", "c3"],
                    "exam_focus": [{"concept_id": "c3", "why": "asked often"}]}}


class WhatAPlanFindingIs(unittest.TestCase):
    def test_every_money_finding_asked_the_plan_for_the_teaching(self):
        for where, problem in MONEY_PLAN_FINDINGS:
            self.assertFalse(plan_structural_finding(finding(where, problem)), where)

    def test_structure_still_blocks(self):
        for where, problem in STRUCTURAL:
            self.assertTrue(plan_structural_finding(finding(where, problem)), where)
        self.assertTrue(plan_structural_finding(finding("", "something is off")))             # unplaced: fail closed
        self.assertTrue(plan_structural_finding(finding("v2", "the analogy of a leaking bucket does not fit a stock variable")))

    def test_the_wording_of_a_plan_field_is_minor(self):
        self.assertFalse(plan_structural_finding(finding("v4: opening_hook", "The hook could be sharper.")))
        self.assertFalse(plan_structural_finding(finding("chapter_flow", "The flow paragraph repeats the titles.")))


class ThePlanReview(unittest.TestCase):
    def test_the_money_plan_replayed_passes_at_round_0(self):
        for chunk in (MONEY_PLAN_FINDINGS[:5], MONEY_PLAN_FINDINGS[5:13], MONEY_PLAN_FINDINGS[13:]):
            self.assertEqual(plan_review_problems(review([finding(w, p) for w, p in chunk])), [])

    def test_structural_findings_come_back_as_remake_instructions(self):
        problems = plan_review_problems(review([finding(*STRUCTURAL[1]), finding(*MONEY_PLAN_FINDINGS[0])]))
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0].startswith("c37: Concept c37 (MDR) is in no video."))
        self.assertEqual(plan_review_problems(review([finding(*STRUCTURAL[0], severity="minor")], verdict="pass")), [])

    def test_a_fail_naming_nothing_still_goes_back_once(self):
        problems = plan_review_problems(review([]))
        self.assertEqual(len(problems), 1)
        self.assertIn("named no blocking finding", problems[0])
        self.assertEqual(plan_review_problems(review([], verdict="pass")), [])

    def test_the_plan_step_reviews_structure_with_the_plans_own_checklist(self):
        step = plan_step(COURSE, small_chapter(), rulebook=BOOK)
        self.assertIs(step.review_problems, plan_review_problems)
        system = step.review_system if isinstance(step.review_system, str) else str(step.review_system)
        self.assertIn("written in the next step, one script per video", system)
        self.assertIn("counts a\nfinding that asks the plan for the teaching as minor", PLAN_REVIEW_HOW)
        checklist = plan_checklist_text(BOOK)
        for rule_id in PLAN_RULES:
            self.assertIn(f"[{rule_id}]", checklist)
        for rule_id in ("S2-02", "S2-04", "S2-05", "S2-06", "S2-07", "S2-08"):
            self.assertNotIn(f"[{rule_id}]", checklist)
            self.assertNotIn(f"[{rule_id}]", system)
        self.assertIn("[S2-01]", system)


if __name__ == "__main__":
    unittest.main()
