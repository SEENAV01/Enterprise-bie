"""Task 045d · the teaching soul (Navin, 24 October 2026): every book line opened, not read out.

Offline: the unpack check of Section 1 (S1-15), the level profiles and the level inferred from the book's text (with the
stop for Navin when they disagree), the script's soul checks (dohraav pakad, clipped notes, the opening question, one recap
per part, flexible pattern steps, the family pattern), the teacher example bank in the prefixes, the explanation library
and its lock tool, the Task 046 benchmark, the dohraav tool, the regression waivers and the fake chain end to end.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

import dohraav  # noqa: E402
import lock_explanations  # noqa: E402
import test_task045_cards as t045  # noqa: E402
from bie.brain import explanations, level, regression, rulebook, soul  # noqa: E402
from bie.brain import content_types as ct  # noqa: E402
from bie.brain import naksha as nk  # noqa: E402
from bie.brain.lesson import (PLAN_HOW, PLAN_ROLE, PLAN_SCHEMA, PLAN_SCHEMA_ID, _prefix, check_script,  # noqa: E402
                              frame_problems, script_prefixes)
from bie.brain.understanding import Course, check_page, page_prefixes  # noqa: E402

BOOK = rulebook.load()
TYPES = ct.load()
LESSON_SET = ROOT / "tests/fixtures/passed_outputs/tissue-t045c-lesson.json.gz"
BENCHMARK = ROOT / "bie/brain/rulebook/benchmarks/epithelium_animation.json"
GOOD_UNPACK = {"terms": [{"term": "absorptive", "plain_meaning": "जहाँ चीज़ें अंदर ली जाती हैं", "everyday_image": "कागज़ पानी सोखता है"}],
               "why_chain": [{"step": "शरीर को खाने से पोषक तत्व अंदर लेने हैं", "basis": "standard"},
                             {"step": "इसके लिए एक पतली परत चाहिए, इसलिए यहाँ epithelium है", "basis": "standard"}],
               "example_or_place": "छोटी आँत की अंदरूनी परत", "consequence": "", "visual_verb": "particles cross the sheet",
               "level_extra": ""}


def words(n, pool):
    return " ".join(pool[i % len(pool)] for i in range(n))


SCHOOL_TEXT = ("Look at your skin. It is made of many small cells. Cells that do the same work stay together. "
               "Such a group of cells is called a tissue. Plants and animals both have tissues. ") * 12
ADVANCED_TEXT = ("Pseudostratified ciliated columnar epithelium demonstrates characteristic basolateral interdigitations; "
                 "immunohistochemical characterisation reveals cytokeratin heterogeneity throughout the tracheobronchial mucosa. ") * 12


# ---------------------------------------------------------------- Section 1: the unpack (S1-15)

class UnpackChecks(unittest.TestCase):
    def item(self, unpack):
        return dict(t045.item("p001-i1", ["p0001-b0001"], "definition", "what", "evidence"), unpack=unpack)

    def test_an_empty_unpack_goes_back_and_a_real_one_passes(self):
        problems = soul.unpack_problems(self.item(None))
        self.assertEqual(len(problems), 1)
        self.assertIn("unpack is empty", problems[0])
        self.assertTrue(problems[0].endswith("(S1-15)"))
        self.assertEqual(soul.unpack_problems(self.item(GOOD_UNPACK)), [])
        self.assertEqual(soul.unpack_elements(GOOD_UNPACK), 4)                 # a term, two why steps, an example

    def test_the_plain_meaning_is_for_the_learner_in_simple_hindi(self):
        roman = dict(GOOD_UNPACK, terms=[{"term": "absorptive", "plain_meaning": "where things are taken in", "everyday_image": "x"}])
        self.assertTrue(any("write it in simple Hindi" in p for p in soul.unpack_problems(self.item(roman))))
        self.assertEqual(soul.unpack_problems(self.item(roman), language="English"), [])
        same = dict(GOOD_UNPACK, terms=[{"term": "Absorptive", "plain_meaning": "absorptive", "everyday_image": ""}])
        self.assertTrue(any("only repeats the term" in p for p in soul.unpack_problems(self.item(same))))

    def test_every_why_step_names_its_basis_and_the_level_bounds_the_chain(self):
        no_basis = dict(GOOD_UNPACK, why_chain=[{"step": "क्योंकि ऐसा है", "basis": "guess"}])
        self.assertTrue(any("names its basis" in p for p in soul.unpack_problems(self.item(no_basis))))
        school = level.load().get("school")
        self.assertTrue(any("opens at most 1" in p for p in soul.unpack_problems(self.item(GOOD_UNPACK), profile=school)))
        revision = level.load().get("revision")
        self.assertTrue(any("adds no new terms" in p for p in soul.unpack_problems(self.item(GOOD_UNPACK), profile=revision)))
        upsc = level.load().get("upsc_pcs")
        self.assertEqual(soul.unpack_problems(self.item(GOOD_UNPACK), profile=upsc), [])

    def test_textbook_hindi_in_an_unpack_goes_back_with_the_english_term_named(self):
        """Job A, 24 October 2026: page 2's plain meanings said ऊतक, कोशिका, उपकला; the learner hears tissue, cell, epithelium."""
        from bie.brain import hinglish
        self.assertEqual(hinglish.technical_words("जानवरों के शरीर में मिलकर काम करने वाले कोशिका-समूह और ऊतकों की परत"),
                         [("कोशिका", "cell"), ("ऊतकों", "tissue")])
        self.assertEqual(hinglish.technical_words("संयोजी ऊतक (connective tissue) सहारा देता है"), [("संयोजी", "connective"), ("ऊतक", "tissue")])
        self.assertEqual(hinglish.technical_words("एक जैसे cells का समूह; प्रकाश संश्लेषण"), [("प्रकाश संश्लेषण", "photosynthesis")])
        self.assertEqual(hinglish.technical_words("tissue yaani ek jaise cells ka group"), [])
        textbook = dict(GOOD_UNPACK, terms=[{"term": "epithelium", "plain_meaning": "उपकला ऊतक की पतली परत", "everyday_image": "x"}])
        problems = [p for p in soul.unpack_problems(self.item(textbook)) if "textbook Hindi" in p]
        self.assertEqual(len(problems), 1)
        self.assertIn("उपकला → epithelium, ऊतक → tissue", problems[0])
        self.assertTrue(problems[0].endswith("(S1-15)"))
        self.assertEqual([p for p in soul.unpack_problems(self.item(textbook), language="English") if "textbook" in p], [])
        self.assertEqual([p for p in soul.unpack_problems(self.item(GOOD_UNPACK)) if "textbook" in p], [])
        self.assertEqual(len(hinglish.load().technical), 62)
        self.assertIn("simple_hindi@2026-10-24.1", BOOK.version)

    def test_check_page_sends_an_unopened_teachable_item_back(self):
        page = t045.Page(1, (t045.Block("p0001-b0001", "Epithelium is found on absorptive and secretive surfaces.", (0, 0, 1, 1)),))
        value = {"notes": {}, "page_summary": "", "boilerplate_block_ids": [], "text_image_disagreements": [],
                 "items": [self.item(None)]}
        self.assertTrue(any("unpack is empty" in p for p in check_page(value, page)))
        value["items"][0]["unpack"] = GOOD_UNPACK
        self.assertEqual([p for p in check_page(value, page) if "S1-15" in p], [])

    def test_the_unpack_is_carried_as_prompt_lines_and_a_naksha_cell(self):
        lines = soul.unpack_lines(GOOD_UNPACK)
        self.assertEqual(lines[0], "  term | absorptive | yaani जहाँ चीज़ें अंदर ली जाती हैं | image: कागज़ पानी सोखता है")
        self.assertTrue(lines[1].startswith("  why | ") and "[standard]" in lines[1])
        self.assertEqual(soul.unpack_short(GOOD_UNPACK), "terms: absorptive; why 2; eg; visual")
        self.assertEqual(soul.unpack_short(None), "")
        chapter = t045.small_chapter()
        rows = {r[0]: r for r in nk.build(chapter)["items"]}
        self.assertEqual(nk.build(chapter)["columns"]["items"][-1], "unpack")
        self.assertEqual(len(rows["p001-i1"]), 7)


# ---------------------------------------------------------------- the level: profiles, inference, disagreement

class LevelProfiles(unittest.TestCase):
    def test_the_profiles_load_and_prefix_text_is_fixed(self):
        profiles = level.load()
        self.assertEqual(sorted(profiles.profiles), ["neet_11_12", "revision", "school", "upsc_pcs"])
        self.assertEqual(profiles.default, "upsc_pcs")
        text = profiles.get("school").prefix_text()
        self.assertTrue(text.startswith("Level profile: School (class 6-10)"))
        self.assertIn("- Why: 1 step(s)", text)
        self.assertIn("- Revision: one line per item", profiles.get("revision").prefix_text())
        with self.assertRaises(KeyError):
            profiles.get("phd")

    def test_the_setting_names_a_level_by_its_words_or_explicitly(self):
        profiles = level.load()
        self.assertEqual(profiles.from_setting(Course("T", "Science", "Class 9 students", "board exam", "Hinglish"))[0], "school")
        self.assertEqual(profiles.from_setting(Course("T", "Biology", "NEET aspirants", "NEET", "Hinglish"))[0], "neet_11_12")
        self.assertEqual(profiles.from_setting(t045.COURSE)[0], "upsc_pcs")
        self.assertEqual(profiles.from_setting(Course("T", "S", "learners", "their exam", "Hinglish"))[0], None)
        self.assertEqual(profiles.from_setting(Course("T", "S", "learners", "their exam", "Hinglish", level="revision")),
                         ("revision", "course.level = revision"))
        self.assertEqual(Course("T", "S", "learners", "their exam", "Hinglish").profile().id, "upsc_pcs")
        self.assertEqual(replace(t045.COURSE, level="school").profile().id, "school")

    def test_the_book_text_gives_its_band_by_markers_then_by_word_length(self):
        self.assertEqual(level.infer_band("Science, Textbook for Class IX. Chapter 6: Tissues.")[0], "school")
        self.assertEqual(level.infer_band("Biology for NEET and Class XI")[0], "senior_secondary")
        self.assertEqual(level.infer_band("Histology of epithelial tissue for MBBS first year")[0], "advanced")
        self.assertEqual(level.infer_band("Indian Polity for UPSC prelims")[0], "exam_general")
        band, evidence = level.infer_band(SCHOOL_TEXT)
        self.assertEqual(band, "school", evidence)
        band, evidence = level.infer_band(ADVANCED_TEXT)
        self.assertEqual(band, "advanced", evidence)
        self.assertGreaterEqual(evidence["long_share"], 0.145)
        band, evidence = level.infer_band("Too little text here.")
        self.assertIsNone(band)
        self.assertIn("only 4 words", evidence["reason"])

    def test_the_real_tissue_chapter_reads_as_senior_secondary_and_fits_upsc(self):
        passed = regression.load(LESSON_SET)
        text = "\n".join(text for entry in passed["pages"] for _, text in entry["blocks"])
        band, evidence = level.infer_band(text)
        self.assertEqual(band, "senior_secondary", evidence)
        chosen = level.choose(Course(**passed["course"]), text)
        self.assertEqual((chosen.profile_id, chosen.source, chosen.disagreement), ("upsc_pcs", "setting", None))

    def test_a_disagreement_stops_for_navin_unless_he_trusts_the_setting(self):
        upsc = t045.COURSE
        chosen = level.choose(upsc, ADVANCED_TEXT)
        self.assertEqual(chosen.band, "advanced")
        self.assertIn("Ask Navin which level to teach at", chosen.disagreement)
        self.assertIn("--level <id> --trust-level", chosen.disagreement)
        self.assertIsNone(level.choose(upsc, ADVANCED_TEXT, trust_setting=True).disagreement)
        school = Course("T", "Science", "Class 9 students", "board exam", "Hinglish")
        self.assertIn("reads as senior_secondary", level.choose(school, "Biology for NEET and Class XI").disagreement)
        self.assertIsNone(level.choose(school, SCHOOL_TEXT).disagreement)
        nothing = Course("T", "S", "learners", "their exam", "Hinglish")
        inferred = level.choose(nothing, SCHOOL_TEXT)
        self.assertEqual((inferred.profile_id, inferred.source, inferred.disagreement), ("school", "inferred", None))
        defaulted = level.choose(nothing, ADVANCED_TEXT)
        self.assertEqual((defaulted.profile_id, defaulted.source), ("upsc_pcs", "default"))
        self.assertIn("deeper than any level profile", defaulted.disagreement)
        self.assertEqual(level.choose(nothing, "").as_dict()["source"], "default")

    def test_the_profile_shapes_the_page_and_script_prefixes(self):
        page_text = page_prefixes(replace(t045.COURSE, level="school"), BOOK)[0].text
        self.assertIn("Level profile: School (class 6-10)", page_text)
        self.assertIn("How real teachers open a book line (teacher example bank", page_text)
        self.assertNotIn("Level profile: UPSC", page_text)
        script_text = script_prefixes(t045.COURSE, BOOK)[0].text
        self.assertIn("Level profile: UPSC / State PCS", script_text)
        self.assertIn("Slender yaani long aur narrow", script_text)
        self.assertIn("[S2-07]", script_text)
        self.assertNotIn("[S3-06]", script_text)
        plan_text = _prefix(t045.COURSE, BOOK, "plan_videos", PLAN_SCHEMA_ID, PLAN_SCHEMA, PLAN_ROLE,
                            PLAN_HOW + "\n\n" + t045.COURSE.profile().prefix_text()).text
        self.assertIn("Level profile: UPSC / State PCS", plan_text)


class LevelInTheRun(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        lines = [["This chapter is written for MBBS first year students.", "Epithelium covers organs.", "1. Simple", "2. Compound"]]
        self.pdf = Path(self.tmp.name, "mbbs.pdf")
        self.pdf.write_bytes(t045.positioned_text_pdf([[(72, 720 - i * 20, t) for i, t in enumerate(page)] for page in lines]))

    def args(self, out, *extra):
        return ["--fake", "--section", "understand", "--source", str(self.pdf), "--out", str(Path(self.tmp.name, out)), "--workers", "1",
                "--course", "title=T;subject=Biology;learners=Class 9 students;exam=board;language=Hinglish", "--max-inr", "100000", *extra]

    def read(self, out, name):
        return json.loads(Path(self.tmp.name, out, name).read_text(encoding="utf-8"))

    def test_a_book_deeper_than_the_setting_stops_before_any_call(self):
        code, printed = t045.run(self.args("stop"))
        self.assertEqual(code, 0)                                   # graceful, like a budget stop
        summary = self.read("stop", "SUMMARY.json")
        self.assertEqual(summary["status"], "stopped: level")
        self.assertEqual(summary["level"]["band"], "advanced")
        self.assertIn("Ask Navin", summary["error"])
        self.assertEqual(summary["preflight"], {"passed": False, "routes": {}, "skipped": "stopped: level"})
        self.assertEqual(summary["ledger_calls"], 0)
        self.assertFalse(Path(self.tmp.name, "stop", "chapter_map.json").exists())
        self.assertIn("level disagreement", printed)

    def test_navins_answer_runs_at_his_level_and_is_recorded(self):
        code, _ = t045.run(self.args("ok", "--level", "school", "--trust-level"))
        self.assertEqual(code, 0)
        summary = self.read("ok", "SUMMARY.json")
        self.assertEqual(summary["status"], "ok")
        self.assertEqual((summary["level"]["profile"], summary["level"]["source"]), ("school", "course"))
        chapter = self.read("ok", "chapter_map.json")
        self.assertEqual(chapter["course"]["level"], "school")
        self.assertEqual(chapter["level"], "school")
        items = [i for i in chapter["items"].values() if i.get("teachable")]
        self.assertTrue(items and all(soul.unpack_elements(i["unpack"]) >= 1 for i in items))
        self.assertEqual(chapter["quality"]["items_unpacked"], len(items))
        with self.assertRaises(SystemExit):
            t045.run(self.args("bad", "--course", "level=phd"))


# ---------------------------------------------------------------- Section 2: the soul of the script (S2-07)

ITEMS = {"p001-i1": {"content": "Collenchyma has unevenly thickened cell walls at the corners and provides flexibility to plants.",
                     "parent_item_id": ""},
         "p001-i2": {"content": "Sclerenchyma cells are dead and have lignified secondary walls.", "parent_item_id": ""}}


def beat(bid, say, *, covers=("p001-i1",), purpose="explain", part="c1.1", step=1):
    return {"beat_id": bid, "part_id": part, "step": step, "purpose": purpose, "say": say, "covers_item_ids": list(covers),
            "answers": [], "on_screen": "", "basis": "book"}


class ScriptSoulChecks(unittest.TestCase):
    RESTATED = "Collenchyma के cell walls corners पर unevenly thickened होते हैं और यह plants को flexibility provides करता है।"

    def test_markers_in_hindi_and_roman(self):
        self.assertEqual(soul.markers("Slender यानी लंबा और पतला।"), ["yaani"])
        self.assertEqual(soul.markers("Yeh isliye hai kyunki cells bahar hain, jaise ..."), ["why", "example"])
        self.assertEqual(soul.markers("लेकिन compound ka kaam protection hai।"), ["contrast"])
        self.assertEqual(soul.markers("Collenchyma flexible hai."), [])

    def test_dohraav_pakad_sends_a_restated_book_line_back_and_an_opened_one_passes(self):
        restated = [beat("b1", self.RESTATED)]
        problems = soul.restatement_problems(restated, ITEMS)
        self.assertEqual(len(problems), 1)
        self.assertIn("content words are the book's own and it opens nothing", problems[0])
        self.assertTrue(problems[0].endswith("(S2-07)"))
        opened = [beat("b1", self.RESTATED + " Unevenly thickened यानी कोनों पर मोटी, जैसे कमरे के कोनों में लगी लकड़ी।")]
        self.assertEqual(soul.restatement_problems(opened, ITEMS), [])
        short = [beat("b1", "Collenchyma flexible होता है।")]                      # too few content words to be a restatement
        self.assertEqual(soul.restatement_problems(short, ITEMS), [])
        hook = [beat("b1", self.RESTATED, purpose="hook")]                        # a hook is not judged
        self.assertEqual(soul.restatement_problems(hook, ITEMS), [])
        share = soul.dohraav_share(restated + opened + short + hook, ITEMS)
        self.assertEqual((share["beats"], share["judged"], share["restating"], share["opened"]), (4, 3, 1, 1))
        self.assertEqual(share["restating_beats"], ["b1"])

    def test_clipped_notes_are_caught_and_teacher_beats_stay(self):
        clipped = soul.clipped_sentences("Chain: flexible walls, supported bending, tendrils और climber stems।")
        self.assertEqual(len(clipped), 1)
        self.assertEqual(soul.clipped_sentences("Labels: living, elongated, irregular corner thickening, बहुत कम intercellular space।"),
                         ["Labels: living, elongated, irregular corner thickening, बहुत कम intercellular space।"])
        for say in ("सही answer a, Loss of heat from our body है।",                 # a verb before the danda
                    "Irregular walls. कैसी? Irregular.",                            # ask and repeat
                    "Permanent का मतलब हमेशा जीवित नहीं।",                            # opens a term
                    "ये सामने क्या दिख रहा है?",                                      # a question
                    "अब इन तीनों को साथ देखो।"):                                     # an order is a verb
            self.assertEqual(soul.clipped_sentences(say), [], say)
        problems = soul.clipped_problems([beat("b1", "Chain: flexible walls, supported bending, tendrils और climber stems।")])
        self.assertTrue(problems and "clipped note without a verb" in problems[0] and problems[0].endswith("(S2-07)"))

    def test_a_spoken_beat_with_textbook_hindi_goes_back_even_with_a_bracket(self):
        from bie.brain.lesson import spoken_problems
        bad = [beat("b1", "संयोजी ऊतक (connective tissue) शरीर को सहारा देता है और जोड़ता है।")]
        problems = spoken_problems(bad, "Hinglish")
        self.assertTrue(any("textbook Hindi" in p and "ऊतक → tissue" in p and p.endswith("(S2-04)") for p in problems), problems)
        good = [beat("b1", "Connective tissue शरीर को सहारा देता है और जोड़ता है।")]
        self.assertEqual([p for p in spoken_problems(good, "Hinglish") if "textbook" in p], [])

    def test_a_topic_opens_with_a_question_and_recaps_are_not_repeated(self):
        parts = [{"part_id": "c1.1"}, {"part_id": "c1.2"}, {"part_id": "c2.1"}]
        beats = [beat("b0", "आज क्या देखेंगे?", purpose="hook", part="", covers=()),
                 beat("b1", "यह collenchyma है, यानी मुड़ने वाला सहारा।"),
                 beat("b2", "अब c1.2 देखो।", part="c1.2"),
                 beat("b3", "Sclerenchyma मज़बूत है।", part="c2.1", covers=("p001-i2",))]
        problems = soul.opening_problems(beats, parts)
        self.assertEqual(len(problems), 1)
        self.assertIn("the topic c2 opens without a question", problems[0])
        beats[3]["say"] = "तने को इतना सख़्त क्या बनाता है? Sclerenchyma।"
        self.assertEqual(soul.opening_problems(beats, parts), [])
        recaps = [beat("r1", "x", purpose="recap"), beat("r2", "y", purpose="recap"), beat("r3", "z", purpose="recap", part="")]
        problems = soul.recap_problems(recaps)
        self.assertEqual(len(problems), 1)
        self.assertIn("beats r1, r2 are all recaps of part c1.1", problems[0])
        self.assertEqual(soul.recap_problems(recaps[1:]), [])

    def test_pattern_steps_are_flexible_only_with_a_real_reason(self):
        card_parts = [{"part_id": "c1.1", "type": "classification"}]
        good = [{"part_id": "c1.1", "skipped_steps": [{"step": 4, "why": "the book names no trick and the family has two members"}]}]
        problems, skipped = soul.skipped_step_problems(good, card_parts, TYPES)
        self.assertEqual((problems, skipped), ([], {"c1.1": {4: "the book names no trick and the family has two members"}}))
        bad = [{"part_id": "c1.1", "skipped_steps": [{"step": 9, "why": "not in the book at all"}, {"step": 2, "why": "no"},
                                                      {"step": 3, "why": "the members are one"}]}]
        problems, _ = soul.skipped_step_problems(bad, card_parts, TYPES)
        self.assertTrue(any("3 of 4 pattern steps skipped" in p for p in problems))
        self.assertTrue(any("step 9 is not a step of its pattern (1-4)" in p for p in problems))
        self.assertTrue(any("needs a real reason, not 'no'" in p for p in problems))

    def test_the_classification_pattern_is_the_family(self):
        pattern = TYPES.pattern("classification")
        self.assertEqual(len(pattern), 4)
        self.assertTrue(pattern[0].startswith("the overview tree first"))
        self.assertIn("layer and shape, why it is named so", pattern[1])
        self.assertIn("memory trick", pattern[3])


class ScriptChecksOnTheCard(unittest.TestCase):
    """The soul checks inside check_script, on the Section 2 fixtures of the Task 045 tests."""

    def setUp(self):
        self.fixture = t045.SectionTwoOnTheCard("test_a_good_script_passes_every_check")
        self.fixture.setUp()
        self.video = self.fixture.plan["videos"][0]

    def check(self, value):
        return check_script(value, self.fixture.chapter, self.video, "Hinglish", self.fixture.card)

    def test_the_good_script_passes_and_each_soul_check_catches_its_fault(self):
        self.assertEqual(self.check(self.fixture.good()), [])
        no_question = self.fixture.good()
        for b in no_question["beats"]:
            b["say"] = b["say"].replace("ये सामने क्या दिख रहा है? ", "")
        self.assertTrue(any("opens without a question" in p for p in self.check(no_question)))
        restated = self.fixture.good()
        item = self.fixture.chapter["items"]["p001-i1"]
        item["content"] = "Collenchyma has unevenly thickened cell walls at the corners and provides flexibility to plants."
        first = next(b for b in restated["beats"] if "p001-i1" in b["covers_item_ids"])
        first["say"] = "ये सामने क्या दिख रहा है? Collenchyma के cell walls corners पर unevenly thickened होते हैं और plants को flexibility provides करते हैं।"
        self.assertTrue(any("opens nothing" in p and "S2-07" in p for p in self.check(restated)))
        clipped = self.fixture.good()
        clipped["beats"][2]["say"] += " Chain: flexible walls, supported bending, tendrils और climber stems।"
        self.assertTrue(any("clipped note" in p for p in self.check(clipped)))
        recaps = self.fixture.good()
        for b in recaps["beats"][1:3]:
            b["purpose"] = "recap"
        self.assertTrue(any("one recap is enough" in p for p in self.check(recaps)))

    def test_a_step_skipped_with_a_reason_is_not_missing_and_a_done_step_cannot_be_skipped(self):
        value = self.fixture.good()
        part = value["parts"][0]["part_id"]
        pattern = TYPES.pattern(next(p["type"] for p in self.fixture.card["parts"] if p["part_id"] == part))
        last = len(pattern)
        value["beats"] = [b for b in value["beats"] if not (b["part_id"] == part and b["step"] == last)]
        self.assertTrue(any(f"part {part}" in p and "teaching-pattern steps not taught" in p for p in self.check(value)))
        value["parts"][0]["skipped_steps"] = [{"step": last, "why": "the book gives nothing for this step on this page"}]
        self.assertEqual([p for p in self.check(value) if "not taught" in p], [])
        _, observed = frame_problems(value, self.fixture.card)
        self.assertEqual(observed["skipped_steps"], {part: {last: "the book gives nothing for this step on this page"}})
        value["parts"][0]["skipped_steps"] = [{"step": 1, "why": "the first step is done elsewhere really"}]
        self.assertTrue(any("listed in skipped_steps but beats perform it" in p for p in self.check(value)))


class RealTissueScripts(unittest.TestCase):
    """The measure on the real tissue scripts (job 3, the regression set): the 'before' of Task 045d."""

    def test_dohraav_before_task_045d(self):
        passed = regression.load(LESSON_SET)
        items = passed["map"]["items"]
        total = {"judged": 0, "restating": 0, "opened": 0}
        clipped = 0
        for video in passed["lesson"]["videos"]:
            share = soul.dohraav_share(video["beats"], items)
            for key in total:
                total[key] += share[key]
            clipped += sum(len(soul.clipped_sentences(b["say"])) for b in video["beats"])
        self.assertEqual(total, {"judged": 273, "restating": 80, "opened": 87})       # 29% of the judged beats only restate
        self.assertEqual(clipped, 10)
        waived = regression.changed_rule_problems(passed)
        self.assertTrue(any(c["rule"] == "S2-07" for _, c in waived))
        self.assertTrue(any(c["rule"].startswith("S2-06") for _, c in waived))
        self.assertEqual(regression.check(passed), [])


# ---------------------------------------------------------------- the teacher bank, the rulebook, the library, the benchmark

class TeacherBankAndRulebook(unittest.TestCase):
    def test_the_teacher_examples_load_and_reach_the_prefixes(self):
        bank = soul.load_teacher()
        self.assertEqual(len(bank["opening_steps"]), 7)
        ids = [m["id"] for m in bank["methods"]]
        self.assertEqual(len(ids), 10)
        self.assertIn("navin_absorptive_secretive", ids)
        text = soul.teacher_text()
        self.assertIn("Slender yaani long aur narrow", text)
        self.assertIn("absorptive surface yaani jahan cheezein andar li jaati hain", text)
        self.assertIn("1) a question about something the learner can see, then the name", soul.opening_steps_text())
        subset = soul.teacher_text(ids=("word_root",))
        self.assertIn("Epi yaani upar", subset)
        self.assertNotIn("M2B", subset)

    def test_the_rulebook_carries_the_new_locked_rules_and_data_files(self):
        for name in ("level_profiles@2026-10-24", "teacher_examples@2026-10-24", "explanations@2026-10-24", "vision-2026-10-21@2026-10-21.12"):
            self.assertIn(name, BOOK.version)
        rules = {r.id: r for r in BOOK.rules}
        for rid in ("G-06", "G-07", "S1-15", "S2-07", "S3-06"):
            self.assertEqual(rules[rid].status, "locked", rid)
        self.assertIn("never just read the line out", rules["G-06"].rule.lower())
        self.assertIn("benchmarks/", rules["S3-06"].rule)
        self.assertEqual(rules["S2-07"].sections, ("lesson",))

    def test_the_regression_guard_reads_rulebook_components(self):
        full = "content_types@2026-10-22.2+simple_hindi@2026-10-23.2+vision-2026-10-21@2026-10-21.11"
        self.assertEqual(regression._version(full), (2026, 10, 21, 11))
        self.assertEqual(regression._version(full, "content_types"), (2026, 10, 22, 2))
        self.assertEqual(regression._version("2026-10-21.10"), (2026, 10, 21, 10))
        self.assertEqual(regression._version("2026-10-21.10", "content_types"), ())
        self.assertEqual(regression._version(None), ())
        rules = [c["rule"] for c in regression.RULE_CHANGES]
        self.assertEqual(rules[:3], ["S1-12", "S1-15", "S2-07"])


class ExplanationLibrary(unittest.TestCase):
    def test_locked_entries_are_found_by_term_and_spoken_as_lines(self):
        library = explanations.load()
        found = library.lookup("The epithelium is found on absorptive and secretive surfaces; its cells are slender.")
        self.assertEqual([e.key for e in found], ["absorptive surface", "secretive surface", "slender"])
        self.assertTrue(all(e.status == "locked" and e.source.startswith("Navin") for e in found))
        lines = library.source_lines("a slender cell")
        self.assertTrue(lines.startswith("  locked explanation | slender: yaani लंबा और पतला; image: building का pillar"))
        self.assertEqual(library.lookup("nothing here"), [])
        self.assertEqual(library.lookup("slenderness"), [])                       # a word boundary, not a prefix
        self.assertEqual([e.key for e in library.lookup("Epithelium absorptive aur secretive surfaces par milta hai.")],
                         ["absorptive surface", "secretive surface"])              # Navin's line: the adjectives alone meet the entries
        self.assertEqual([e.key for e in library.lookup("a secretory epithelium")], ["secretive surface"])

    def test_navins_verdict_locks_an_items_unpack_through_the_tool(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder, "explanations.json")
            shutil.copy(explanations.PATH, path)
            chapter = {"course": {"subject": "biology"}, "items": {"p003-i2": {"content": "Cuboidal cells are cube like.",
                       "unpack": dict(GOOD_UNPACK, terms=[{"term": "cuboidal", "plain_meaning": "हर तरफ़ से बराबर, घन जैसा",
                                                           "everyday_image": "लूडो का पासा"}])}},
                       "map": {"concepts": [{"name": "simple cuboidal epithelium", "item_ids": ["p003-i2"]}]}}
            run = Path(folder, "vm-t045d-run")
            run.mkdir()
            run.joinpath("chapter_map.json").write_text(json.dumps(chapter), encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = lock_explanations.main(["--run", str(run), "--items", "p003-i2", "--by", "Navin, 25 October 2026",
                                               "--path", str(path)])
            self.assertEqual(code, 0, out.getvalue())
            library = explanations.load(str(path))
            self.assertEqual(library.version, "2026-10-24.2")
            entry = library.lookup("a cuboidal cell")[0]
            self.assertEqual((entry.plain_meaning, entry.from_run, entry.concepts), ("हर तरफ़ से बराबर, घन जैसा", "vm-t045d-run:p003-i2",
                                                                                     ("simple cuboidal epithelium",)))
            self.assertEqual(len(entry.why_chain), 2)
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertTrue(data["changes"][0].startswith("2026-10-24.2: 1 entries locked by Navin, 25 October 2026"))
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                self.assertEqual(lock_explanations.main(["--run", str(run), "--items", "p009-i9", "--by", "x", "--path", str(path)]), 2)
            self.assertIn("ITEMS_NOT_IN_MAP:p009-i9", err.getvalue())
        explanations.load.cache_clear()
        self.assertEqual(explanations.load().version, "2026-10-24.1")            # the real file is untouched


class Benchmark(unittest.TestCase):
    def test_the_epithelium_benchmark_is_a_shot_list_with_rules_and_blocks(self):
        data = json.loads(BENCHMARK.read_text(encoding="utf-8"))
        self.assertEqual(data["schema"], "bie.brain.benchmark/1")
        self.assertEqual([r["id"] for r in data["rules"]], [f"B-{n:02d}" for n in range(1, 13)])
        blocks = set(data["blocks"]["built_in_task_046"]) | set(data["blocks"]["planned"])
        self.assertEqual(set(data["blocks"]["built_in_task_046"]), {"cell_sheet", "particle_flow", "organ_zoom", "focus_glow",
                                                                   "kinetic_caption", "concept_arrow", "board_build", "mnemonic_card"})
        seconds = [int(m) * 60 + int(s) for m, s in (shot["t"].split(":") for shot in data["shots"])]
        self.assertEqual(seconds, sorted(seconds))
        self.assertEqual((data["shots"][0]["t"], data["shots"][-1]["t"]), ("0:00", "2:30"))
        for shot in data["shots"]:
            self.assertIn(shot["block"], blocks, shot["t"])
            self.assertTrue(2 <= shot["seconds"] <= 7, shot["t"])
            if shot["say"]:
                self.assertTrue(shot["show"], shot["t"])
        self.assertTrue(any("yaani" in shot["say"] for shot in data["shots"]))
        self.assertEqual(BOOK.version.count("benchmark"), 0)                    # the benchmark is not a rulebook file


# ---------------------------------------------------------------- the dohraav tool and the whole chain

class DohraavTool(unittest.TestCase):
    def test_the_tool_measures_a_run_folder_pair(self):
        with tempfile.TemporaryDirectory() as folder:
            first, second = Path(folder, "understand"), Path(folder, "lesson")
            first.mkdir(), second.mkdir()
            first.joinpath("chapter_map.json").write_text(json.dumps({"items": ITEMS}), encoding="utf-8")
            video = {"video_id": "v1", "status": "passed", "card_parts": [{"part_id": "c1.1"}],
                     "beats": [beat("b1", ScriptSoulChecks.RESTATED), beat("b2", "यह यानी मुड़ने वाला सहारा है।"),
                               beat("b3", "Chain: flexible walls, supported bending, tendrils और climber stems।")]}
            second.joinpath("lesson_plan.json").write_text(json.dumps({"videos": [video]}), encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(dohraav.main([str(first), str(second), "--json"]), 0)
            total = json.loads(out.getvalue())[str(second)]["total"]
            self.assertEqual((total["judged"], total["restating"], total["opened"], total["clipped"], total["no_question"]),
                             (3, 1, 1, 1, 1))
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                dohraav.main([str(first), str(second)])
            self.assertIn("Dohraav: 1 of 3 judged beats (33.3%) only restate the book", out.getvalue())
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(dohraav.main([str(second)]), 2)                 # no chapter map before the lesson


class FakeChainWithTheSoul(unittest.TestCase):
    def test_the_chain_writes_unpack_dohraav_and_skipped_steps(self):
        fixture = t045.Chain("test_chain_on_cards_writes_naksha_types_frames_and_records")
        fixture.setUp()
        try:
            code, _ = t045.run(fixture.args("soul"))
            self.assertEqual(code, 0)
            summary = fixture.read("soul", "SUMMARY.json")
            self.assertEqual(summary["status"], "ok")
            self.assertEqual(summary["level"]["profile"], "upsc_pcs")
            quality = summary["lesson_quality"]
            self.assertEqual(quality["videos_passed"], quality["videos"])
            self.assertEqual(set(quality["dohraav"]), {"judged_beats", "restating", "share", "opened_share"})
            lesson = fixture.read("soul", "lesson_plan.json")
            self.assertTrue(all("dohraav" in v for v in lesson["videos"]))
            self.assertTrue(all("skipped_steps" in p for v in lesson["videos"] for p in v["parts"]))
            chapter = fixture.read("soul", "chapter_map.json")
            self.assertEqual(chapter["schema"], "bie.brain.chapter-map/2")
            self.assertTrue(all(i.get("unpack") for i in chapter["items"].values() if i.get("teachable")))
            self.assertGreater(chapter["quality"]["terms_opened"], 0)
            pages = Path(fixture.tmp.name, "soul", "PAGES.md").read_text(encoding="utf-8")
            self.assertIn("khola (unpack)", pages)
            script = Path(fixture.tmp.name, "soul", "SCRIPT.md").read_text(encoding="utf-8")
            self.assertIn("dohraav", script.lower())
        finally:
            fixture.tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
