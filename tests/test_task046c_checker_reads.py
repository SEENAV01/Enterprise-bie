"""Task 046 Part C · work C, second piece: what the Money lesson resume -e taught (29 October 2026; 12 of 18 scripts failed in
the checker's round after every code check had passed, 33 blocking findings).

Offline: S2-09 refuses the state report in every form the checker found (verb-less "wheat 10 से 8 kg", "जेब में 5 से 3",
"receipt ₹0 से ₹100 होती है", "seller को ₹0 से ₹20 मिलते हैं") and leaves ranges and teacher sentences alone; a checker's demand
for a dated source, for the term after an example BIE's S2-08 does not bind, or for a sentence that says what the source lacks
is minor by code (BIE's code passed those checks before the review ran); the checker's card says so; the rulebook, the regression
registry and the passed outputs carry the change.
"""
from __future__ import annotations

import gzip
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain import lesson, regression, rulebook, soul  # noqa: E402


def finding(where, problem, fix=""):
    return {"where": where, "problem": problem, "fix": fix, "severity": "blocking"}


class StateReportInEveryForm(unittest.TestCase):
    def test_the_checkers_forms_are_caught_by_code(self):
        beats = [{"beat_id": "b2", "say": "एक illustrative market में किसान 2 kg wheat देकर 1 metre कपड़ा लेता है। Wheat 10 से 8 kg, कपड़ा 0 से 1 metre हुआ।"},
                 {"beat_id": "b25", "say": "उसी से 1 metre कपड़ा खरीदा; नमक 0 से 1, फिर 0 kg हुआ।"},
                 {"beat_id": "b27", "say": "2 silver coins दिए; जेब में 5 से 3 बचे।"},
                 {"beat_id": "b26", "say": "दुकानदार की इस बिक्री की receipt ₹0 से ₹100 होती है: यह UPI transaction route है।"},
                 {"beat_id": "b28", "say": "सफलता पर ₹500 से ₹480 बचते हैं; seller को ₹0 से ₹20 मिलते हैं।"},
                 {"beat_id": "b51", "say": "Imaginary ₹40 payment में buyer ₹100 से ₹60, merchant ₹0 से ₹40 होता है; unit rupee ही है।"},
                 {"beat_id": "b4", "say": "Transfer होने पर उसका balance ₹3,000 से ₹2,000 और परिवार का ₹200 से ₹1,200 होता है।"},
                 {"beat_id": "b40", "say": "permission used ₹0 से ₹200 होती है; ₹1000 official limit नहीं है।"}]
        problems = soul.state_report_problems(beats)
        self.assertEqual([p.split(":")[0] for p in problems], [f"beat {b['beat_id']}" for b in beats])
        self.assertTrue(all(p.endswith("(S2-09)") and soul.TEACHER_NUMBERS in p for p in problems))

    def test_a_range_a_teacher_sentence_and_a_thousands_comma_are_not_state_reports(self):
        beats = [{"beat_id": "b9", "say": "मान लो payment का minimum ₹100 और maximum ₹1,000 है; ₹100 से ₹1,000 तक चलेगा, ₹99 या ₹1,001 नहीं।"},
                 {"beat_id": "b3", "say": "पहले आपके पास 500 रुपये थे, किराने के 100 दिए, अब 400 बचे।"},
                 {"beat_id": "b5", "say": "इसमें 6 से 8 मिनट लगते हैं; ₹100 से ₹500 के बीच कुछ भी; 10 से 20 तक गिनो।"},
                 {"beat_id": "b6", "say": "₹500 से ₹100 घटाकर ₹400 बचे। दाम ₹50 से बढ़कर ₹65 हो गया। 1 से 2 घंटे में settle होता है।"},
                 {"beat_id": "b7", "say": "कल 2 खरीदार आए, आज 12: दाम ₹50 से बढ़कर ₹65 हो गया।"}]
        self.assertEqual(soul.state_report_problems(beats), [])

    def test_the_passed_outputs_still_have_none(self):
        for path in sorted((ROOT / "tests" / "fixtures" / "passed_outputs").glob("*.json.gz")):
            passed = json.loads(gzip.open(path).read())
            for video in (passed.get("lesson") or {}).get("videos", []):
                self.assertEqual(soul.state_report_problems(video["beats"]), [], f"{path.name}: {video['video_id']}")


class TheCheckerReadAsTheRulesRead(unittest.TestCase):
    def test_a_dated_source_demand_is_minor_after_the_codes_s2_10_passed(self):
        v2 = finding("b34, b39, b43–b44, b62", "Several examinable outside qualifications lack dated sources: cards need not store money, deposits "
                     "are bank claims, legal tender differs from practical acceptance.", "Attach appropriate named, dated sources to retained outside claims.")
        v4 = finding("b28 and b42", "Examinable outside clarifications lack dated attribution and visible outside labels: the pound's historical "
                     "continuity across backing regimes, and the meanings of proof and UNC. A mixed basis tag is not a learner-facing label.")
        v7 = finding("b16", "Modern State/Central Bank backing को silver redemption guarantee से अलग करने वाला examinable outside clarification "
                     "बिना dated source दिया गया है।")
        v14 = finding("b26", "The explanation that biaxial orientation involves stretching the film in two directions is an examinable outside "
                      "manufacturing fact, but no dated source is named.", "Attach a suitable named, dated source to this beat.")
        self.assertEqual([lesson.script_finding_minor(f) for f in (v2, v4, v7, v14)], ["source"] * 4)
        content = finding("c31.2, b31–b35", "The comparison excludes payment app, bank transfer and digital currency without opening what each is.",
                          "Briefly contrast the app as an interface. Use dated sources for outside factual explanations.")
        self.assertEqual(lesson.script_finding_minor(content), "")                  # the problem is the content; the fix only mentions sources

    def test_an_example_first_demand_is_minor_unless_the_example_itself_is_faulted(self):
        v3 = finding("b7–b9", "Standardization is named in b8 before its example runs. The grain transaction demonstrates portability and acceptance.")
        v10 = finding("b1 and b6; p011-i17 and p012-i1", "The cheque term is named before its numerical example has run: the hook names it, and b6 "
                      "uses the name before presentation, clearing and balance changes are completed. This fails the explicit economics example-first rule.")
        v2 = finding("b28, before b36–b38", "The intrinsic-value concept is taught as gold and silver having their own material value before its "
                     "numerical example runs. Avoiding the exact term does not satisfy the example-first requirement.")
        self.assertEqual([lesson.script_finding_minor(f) for f in (v3, v10, v2)], ["example-first"] * 3)
        v4 = finding("c10.2, b23–b25", "Monetary policy is named before its example, and the subsequent loan-expansion example has no numbers.")
        self.assertEqual(lesson.script_finding_minor(v4), "")                        # the example itself is faulted: the checker's call stands

    def test_a_fix_that_says_what_the_source_lacks_is_minor_and_content_findings_stand(self):
        v2 = finding("b35; p002-i12#q1", "The beat claims to answer the whole book question but supplies only the sequence. It never answers "
                     "whether the sequence provides dates.", "Add a short clarification that this is an undated schematic sequence, not a dated universal history.")
        self.assertEqual(lesson.script_finding_minor(v2), "w01")
        for f in (finding("b2, b25, b27", "Parts of the numerical narration still report ledger states rather than tell what happened: 'Wheat 10 से 8 kg'."),
                  finding("b41–b44", "Several new terms and exam qualifications are compressed into label-like assertions. Portability is not plainly defined."),
                  finding("b13–b19", "The one-₹2,000-for-four-₹500 transaction is run in b13, run again in b15, and restated in b17."),
                  finding("b18; c23.3; p011-i10", "UPI, debit cards, NEFT and RTGS are only named. The learner is never shown how these routes move the deposit money."),
                  finding("b4, b6–b7", "Several lines teach the layout of the source rather than the payment arrangement: 'Diagram में भी', 'इस तस्वीर में'.")):
            self.assertEqual(lesson.script_finding_minor(f), "", f["problem"][:60])

    def test_the_script_passes_when_every_blocking_finding_was_such_and_the_record_says_why(self):
        review = {"verdict": "fail", "problems": [
            finding("b22", "The explanation that punch-marked coins receive marks through punches is outside historical knowledge, but this "
                    "mixed-basis beat has no dated source."),
            finding("b7–b9", "Standardization is named in b8 before its example runs."),
            {"where": "maker notes", "problem": "The notes describe a patch history.", "fix": "", "severity": "minor"}]}
        self.assertEqual(lesson.script_review_problems(review, {}), [])
        self.assertEqual(review["verdict"], "pass")
        self.assertEqual([f.get("minor_by_code") for f in review["problems"]], ["source", "example-first", None])
        review = {"verdict": "fail", "problems": [finding("b16", "Outside clarification without a dated source."),
                                                  finding("b14 and b51", "The examples still report balance states rather than narrating transactions.")]}
        problems = lesson.script_review_problems(review, {})
        self.assertEqual(len(problems), 1)
        self.assertIn("balance states", problems[0])
        self.assertEqual(review["verdict"], "fail")

    def test_the_checkers_card_says_so(self):
        for text in ("never ask for sources on other", "a hook or a question may name", "never ask the script to say what the source lacks"):
            self.assertIn(text, lesson.SCRIPT_REVIEW_HOW)


class TheVmJobMayAskForMoreRounds(unittest.TestCase):
    def test_max_rounds_up_to_six_the_default_still_three(self):
        from tools import codex_vm
        job = {"job": codex_vm.JOB_SCHEMA, "id": "t046c-money-lesson-f", "section": "lesson", "chapter_map": "https://example.org/m.json",
               "maker": "codex", "reviewer": "codex", "max_inr": 5}
        self.assertEqual(codex_vm.validate(job)["max_rounds"], 3)
        self.assertEqual(codex_vm.validate(dict(job, max_rounds=5))["max_rounds"], 5)
        with self.assertRaises(codex_vm.JobError):
            codex_vm.validate(dict(job, max_rounds=7))


class RulebookAndRegistry(unittest.TestCase):
    def test_the_rulebook_carries_the_change(self):
        vision = json.loads((ROOT / "bie/brain/rulebook/vision-2026-10-21.json").read_text(encoding="utf-8"))
        self.assertEqual(vision["version"], "2026-10-21.17")
        rules = {r["id"]: r for r in vision["rules"]}
        self.assertIn("without one", rules["S2-09"]["rule"])
        self.assertIn("minor by code", rules["S2-10"]["rule"])
        self.assertIn("minor by code", rules["S2-08"]["rule"])
        self.assertTrue(vision["changes"][-1].startswith("2026-10-21.17"))
        self.assertIn("vision-2026-10-21@2026-10-21.17", rulebook.load().version)

    def test_the_regression_registry_explains_a_new_s2_09_finding_on_an_earlier_passed_script(self):
        old = {"rulebook": "visual_grammar@2026-10-29.1+vision-2026-10-21@2026-10-21.16"}
        changed = regression._changed(old, "beat b2: 'Wheat 10 से 8 kg' reports a state like a ledger (S2-09)")
        self.assertEqual(changed["rule"], "S2-09")
        self.assertEqual(changed["rulebook"], f"{regression.VISION}@2026-10-21.17")
        new = {"rulebook": "visual_grammar@2026-10-29.1+vision-2026-10-21@2026-10-21.17"}
        self.assertIsNone(regression._changed(new, "beat b2: x (S2-09)"))


if __name__ == "__main__":
    unittest.main()
