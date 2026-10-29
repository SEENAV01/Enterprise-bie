"""Task 046 Part C · seekh from the Money lesson resume (``t046c-money-lesson-c``, 28 October 2026; SEEKH_LOG entry 22).

Of the 11 scripts that failed, 3 failed on the maker's notes (v2, v5, v17; v5 and v17 on nothing else): a resume started a
script with ``notes: None``, so the first patch round's notes ("targeted wording correction in b12") became the script's notes
for good and the checker failed three rounds on them. 3 failed on time the code had passed (v2 11.1 against 11.0, v11 10.5
against 10.4, v14 8.9 against 8.8). v17, passed in run b, was lost to the W-01 pattern ``answer codes?`` catching the exam's
own "answer code चुनिए". Now: lesson_plan.json keeps each script's notes and a resume starts from them; a finding only on the
notes, or one that re-measures time, is minor (the script passes when nothing else is blocking); W-01 catches only the
source-pointing forms; सफर is an everyday word. Offline, no network, no keys, no money.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain import hinglish, lesson, rulebook, soul  # noqa: E402
from bie.brain.runner import merge_notes  # noqa: E402

BOOK = rulebook.load()
UNIT_NOTES = {"about": "NPCI, RuPay and MDR: who pays whom in a card payment.", "key_questions": ["Who receives the MDR?"],
              "decisions": [{"decision": "Run the ₹1,000 purchase first.", "reason": "S2-08"}], "uncertain": []}
PATCH_NOTES = {"about": "Targeted wording correction in b12; all other teaching content remains unchanged.",
               "key_questions": ["How should both NPCI statements be evaluated?"],
               "decisions": [{"decision": "Replaced 'answer code चुनिए' with 'सही combination चुनिए' in b12 only.", "reason": "W-01"}],
               "uncertain": []}


def finding(where, problem, severity="blocking"):
    return {"where": where, "problem": problem, "fix": "fix it", "severity": severity}


class NotesTravel(unittest.TestCase):
    def test_a_resume_starts_from_the_earlier_notes_not_from_none(self):
        entry = {"video_id": "v17", "title": "t", "notes": UNIT_NOTES, "parts": [], "beats": [{"beat_id": "b1", "say": "x", "subtitle": "x", "voice": "x"}]}
        value = lesson._script_value(entry)
        self.assertEqual(value["notes"], UNIT_NOTES)
        self.assertEqual(list(value["beats"][0]), ["beat_id", "say"])
        self.assertIsNone(lesson._script_value({"video_id": "v1", "beats": []})["notes"])     # an older run without notes

    def test_the_patch_notes_never_replace_the_units_about(self):
        merged = merge_notes(UNIT_NOTES, PATCH_NOTES)
        self.assertEqual(merged["about"], UNIT_NOTES["about"])
        self.assertEqual(merged["key_questions"], UNIT_NOTES["key_questions"])
        self.assertEqual(len(merged["decisions"]), 2)
        self.assertEqual(merge_notes(None, PATCH_NOTES), PATCH_NOTES)                           # the fault: nothing to keep


class FindingsReadAsTheRulesRead(unittest.TestCase):
    def test_a_finding_only_on_the_notes_is_minor(self):
        for where in ("notes.about, notes.key_questions, notes.decisions", "notes", "maker notes", "Video v2; maker notes",
                      "notes.about; notes.key_questions; notes.decisions[0–1]", "The maker's notes"):
            self.assertEqual(lesson.script_finding_minor(finding(where, "The notes document only a b12 wording correction.")), "notes", where)
        for where in ("b12", "Video v11; notes.decisions; b23–b34", "c28.3, b28", "b7a and b8, on_screen"):
            self.assertEqual(lesson.script_finding_minor(finding(where, "The required difference-table recap is missing.")), "", where)

    def test_a_finding_that_re_measures_time_is_minor(self):
        v2 = finding("Video v2; maker notes", "BIE measures 11.1 spoken minutes against an allowed maximum of 11.0. The notes claim a "
                     "reduction below the limit, but that is not the supplied measurement.")
        v11 = finding("Video v11; notes.decisions; b23–b34", "BIE measures 10.5 spoken minutes against the permitted maximum of 10.4.")
        v14 = finding("Video v14; b19–b23", "Measured narration is 8.9 minutes, exceeding the supplied 8.8-minute ceiling. The two "
                      "consecutive standardized-connection models repeat the same mechanism.")
        self.assertEqual([lesson.script_finding_minor(f) for f in (v2, v11, v14)], ["notes", "time", "time"])
        content = finding("b15–b19", "The exchange result is repeatedly restated: b17 repeats b15's arithmetic.")
        self.assertEqual(lesson.script_finding_minor(content), "")
        example = finding("b19–b21", "Indivisibility is named after a cow question without an actual small-purchase example; 5 minutes "
                          "of the part open nothing.")
        self.assertEqual(lesson.script_finding_minor(example), "")                                 # minutes without a ceiling: content

    def test_the_script_passes_when_every_blocking_finding_was_such(self):
        review = {"verdict": "fail", "problems": [finding("notes.about, notes.key_questions, notes.decisions", "The notes still describe a targeted b13 repair.")]}
        self.assertEqual(lesson.script_review_problems(review, {}), [])
        self.assertEqual(review["verdict"], "pass")
        self.assertEqual(review["problems"][0]["severity"], "minor")
        self.assertEqual(review["problems"][0]["minor_by_code"], "notes")
        review = {"verdict": "fail", "problems": [finding("Video v11; notes.decisions; b23–b34", "BIE measures 10.5 spoken minutes against the permitted maximum of 10.4."),
                                                  finding("b23, b24, b27", "The payment sequence is repeatedly walked through and recapped.")]}
        problems = lesson.script_review_problems(review, {})
        self.assertEqual(len(problems), 1)
        self.assertIn("repeatedly walked through", problems[0])
        self.assertEqual(review["verdict"], "fail")
        plain = {"verdict": "fail", "problems": [finding("b12", "points at the source rather than teaching the fact.")]}
        self.assertEqual(len(lesson.script_review_problems(plain, {})), 1)
        self.assertEqual(lesson.script_review_problems({"verdict": "pass", "problems": []}, {}), [])

    def test_the_script_step_uses_the_filter_and_the_prompt_says_so(self):
        import inspect
        self.assertIn("review_problems=script_review_problems", inspect.getsource(lesson.script_step))
        self.assertIn("a problem only in the notes is minor", lesson.SCRIPT_REVIEW_HOW)
        self.assertIn("never report the length as a problem", lesson.SCRIPT_REVIEW_HOW)


class WordingAndWords(unittest.TestCase):
    def test_w01_catches_only_the_source_pointing_answer_codes(self):
        beat = lambda say: [{"beat_id": "b12", "say": say}]
        self.assertEqual(soul.wording_problems(beat("इसलिए पहले हर statement का सही या गलत होना तय कीजिए, फिर answer code चुनिए।")), [])
        self.assertEqual(soul.wording_problems(beat("The answer codes (a) to (d) are the exam's own.")), [])
        self.assertEqual(len(soul.wording_problems(beat("The answer codes in the original continuation give the pairing."))), 1)
        self.assertEqual(len(soul.wording_problems(beat("Use the supplied answer codes for the pairing."))), 1)
        self.assertEqual(len(soul.wording_problems(beat("Supplied figure के हिसाब से RBI ने 1935 में notes छापे।"))), 1)

    def test_safar_is_everyday_and_the_formal_words_stay_hard(self):
        self.assertEqual(hinglish.difficult_words("Rupee का सफर silver coins से Digital Rupee तक चला।"), [])
        self.assertEqual(hinglish.difficult_words("यह सफ़र लंबा था।"), [])
        self.assertEqual(hinglish.difficult_words("यह एक काल्पनिक और सुलभ उदाहरण है।"), ["काल्पनिक", "सुलभ"])

    def test_the_versions_are_pinned(self):
        self.assertIn("simple_hindi@2026-10-28.1", BOOK.version)
        self.assertIn("visual_grammar@2026-10-29.1", BOOK.version)
        data = json.loads((ROOT / "bie" / "brain" / "rulebook" / "visual_grammar.json").read_text(encoding="utf-8"))
        self.assertNotIn("answer codes?", data["wording"]["W-01"]["english"])
        self.assertIn("(?:original|source|supplied|given) answer codes?", data["wording"]["W-01"]["english"])


if __name__ == "__main__":
    unittest.main()
