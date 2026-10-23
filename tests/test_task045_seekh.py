"""Task 045 PR B, seekh → BIE: earlier passed outputs stay passed, and the changes learned from the tissue run (offline).

Navin's standing rule (CLAUDE.md, 23 October 2026): after every live run Claude uses what it taught to improve BIE without
asking; every change ships with tests, is measured (docs/roadmap/SEEKH_LOG.md) and may not fail an output that passed
before. The sets in tests/fixtures/passed_outputs/ are BIE's own passed work from live runs (not accepted examples);
every set must pass today's code checks.
"""
from __future__ import annotations

import contextlib
import copy
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests" / "productization" / "document_intelligence"))

import passed_outputs  # noqa: E402
import run_brain  # noqa: E402
from bie.brain import regression, rulebook  # noqa: E402
from bie.brain import content_types as ct  # noqa: E402
from bie.brain.pages import Block  # noqa: E402
from bie.brain.understanding import CONNECT_HOW, PAGE_HOW, Course, page_prefixes  # noqa: E402
from structural_pdf_fixtures import positioned_text_pdf  # noqa: E402

SETS = sorted((ROOT / "tests" / "fixtures" / "passed_outputs").glob("*.json.gz"))
TISSUE = ROOT / "tests" / "fixtures" / "passed_outputs" / "tissue-t045b-understand.json.gz"


def blocks(*texts, page=5):
    return tuple(Block(f"p{page:04d}-b{n:04d}", text, (0, 0, 1, 1)) for n, text in enumerate(texts, 1))


def quiet(function, *args):
    with contextlib.redirect_stdout(io.StringIO()) as out:
        code = function(*args)
    return code, out.getvalue()


class PassedOutputsStayPassed(unittest.TestCase):
    def test_every_saved_set_still_passes_todays_checks(self):
        self.assertTrue(SETS)
        for path in SETS:
            with self.subTest(set=path.name):
                passed = regression.load(path)
                self.assertEqual(passed["schema"], regression.SCHEMA)
                self.assertEqual(regression.check(passed), [])

    def test_the_tissue_set_holds_job_1_whole(self):
        passed = regression.load(TISSUE)
        self.assertEqual([p["page"] for p in passed["pages"]], list(range(1, 15)))
        self.assertTrue(all(p["coverage"] is not None for p in passed["pages"]))      # each page's card, from its record
        self.assertEqual([p["page"] for p in passed["pages"] if not p["coverage"]["must_cover"]], [2, 7, 8])   # image-only pages
        self.assertEqual(len(passed["map"]["map"]["concepts"]), 43)

    def test_the_check_finds_earlier_work_that_no_longer_passes(self):
        passed = copy.deepcopy(regression.load(TISSUE))
        options = {i["item_id"]: i for i in passed["pages"][13]["value"]["items"]}
        options["i1"]["parent_item_id"] = ""            # job 1 round 1 on page 14: an option without its question
        concept = passed["map"]["map"]["concepts"][0]
        concept["content_type"] = "none"                 # job 1 round 1 of the map: eleven concepts typed "none"
        problems = regression.check(passed)
        self.assertIn("page 14: item i1: an answer_option needs its question as parent_item_id", problems)
        self.assertIn(f"map: concept {concept['concept_id']}: give it its main content type, not 'none'", problems)

    def test_the_tool_exits_1_when_a_set_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            bad = copy.deepcopy(regression.load(TISSUE))
            bad["pages"][0]["value"]["items"] = bad["pages"][0]["value"]["items"][:1]
            regression.save(bad, Path(folder, "bad.json.gz"))
            self.assertEqual(quiet(passed_outputs.main, ["check", str(TISSUE)])[0], 0)
            code, out = quiet(passed_outputs.main, ["check", str(TISSUE), str(Path(folder, "bad.json.gz"))])
            self.assertEqual(code, 1)
            self.assertIn('"set": "bad.json.gz"', out)

    def test_export_from_a_run_keeps_only_passed_work_and_checks_it(self):
        with tempfile.TemporaryDirectory() as folder:
            lines = [["There are mainly four different types of tissues present in our body.", "1. Epithelial- provides covering",
                      "2. Muscular- helps in movement"], ["Cells divide by mitosis.", "The heart beats 72 times per minute."]]
            pdf = Path(folder, "chapter.pdf")
            pdf.write_bytes(positioned_text_pdf([[(72, 720 - i * 20, t) for i, t in enumerate(page)] for page in lines]))
            run = Path(folder, "run")
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                code = run_brain.main(["--fake", "--section", "chain", "--source", str(pdf), "--out", str(run), "--workers", "1",
                                       "--max-inr", "100000", "--course",
                                       "title=T;subject=Biology;learners=UPSC;exam=UPSC;language=Hinglish"])
            self.assertEqual(code, 0)
            out = Path(folder, "set.json.gz")
            code, printed = quiet(passed_outputs.main, ["export", "--run", str(run), "--pdf", str(pdf), "--out", str(out),
                                                        "--lesson", str(run)])
            self.assertEqual(code, 0)
            lesson = json.loads(Path(run, "lesson_plan.json").read_text(encoding="utf-8"))
            self.assertEqual(json.loads(printed), {"pages": 2, "map": True, "scripts": len(lesson["videos"])})
            passed = regression.load(out)
            beats = [b for v in passed["lesson"]["videos"] for b in v["beats"]]
            self.assertTrue(beats and not any("subtitle" in b or "voice" in b for b in beats))    # made again from "say"
            self.assertEqual(regression.check(passed), [])
            passed["lesson"]["videos"][0]["beats"] = passed["lesson"]["videos"][0]["beats"][:1]
            self.assertTrue(any(p.startswith("script v1:") for p in regression.check(passed)))


class ListRestartAndColonHeadings(unittest.TestCase):
    """Job 1, pages 4, 5 and 10: two of the code's strong type proposals were wrong for the same two reasons."""

    def test_a_list_that_starts_again_is_a_new_list(self):
        page = blocks("Types:", "a. Skeletal", "b. Smooth", "c. Cardiac", "a. Skeletal Muscle Tissue:", "Characteristics",
                      "• Muscle fibres are elongated and cylindrical")
        got = ct.propose_blocks(page)
        self.assertEqual([got[b.id].type for b in page[1:4]], ["classification"] * 3)
        self.assertNotEqual(got[page[4].id].type, "classification")       # page 5: the first kind's own section
        page = blocks("There are two types of tissues.", "1. Simple", "2. Complex", "1. Parenchyma cells are living.")
        got = ct.propose_blocks(page)
        self.assertEqual([got[b.id].type for b in page[1:3]], ["classification"] * 2)
        self.assertIsNone(got[page[3].id].type)

    def test_roman_numerals_keep_their_list(self):
        page = blocks("There are three types of rocks.", "i. Igneous", "ii. Sedimentary", "iii. Metamorphic", "iv) Others")
        got = ct.propose_blocks(page)
        self.assertEqual([(got[b.id].type, got[b.id].strength) for b in page[1:]], [("classification", "strong")] * 4)
        self.assertEqual([ct._marker(b.text) for b in page[1:]], [("roman", 1), ("roman", 2), ("roman", 3), ("roman", 4)])

    def test_a_line_ending_in_a_colon_is_a_hint_and_still_leads_its_list(self):
        page = blocks(" Connective tissue is made up of :-", "Types:", "a. Skeletal", "TISSUE: Cells combine to perform same function.")
        got = ct.propose_blocks(page)
        heading = got[page[0].id]
        self.assertEqual((heading.type, heading.strength), ("structure", "weak"))
        self.assertIn(ct.INTRO_MARK, heading.evidence)
        self.assertEqual((got[page[1].id].type, got[page[1].id].strength), ("classification", "weak"))
        self.assertEqual((got[page[2].id].type, got[page[2].id].strength), ("classification", "strong"))
        self.assertIn("list under 'Types:'", got[page[2].id].evidence[0])
        self.assertEqual((got[page[3].id].type, got[page[3].id].strength), ("definition", "strong"))     # a colon inside

    def test_the_maker_is_not_sent_back_for_a_heading_that_introduces_what_follows(self):
        page = blocks(" Connective tissue is made up of :-", page=4)
        item = {"item_id": "i21", "kind": "list_point", "block_ids": [page[0].id], "content_type": "none", "teachable": True}
        row = ct.compare([item], ct.propose_blocks(page))[0]
        self.assertEqual(row["status"], "differs_weak")                # was "disagree" before the colon rule


class InstructionsLearnedFromJob1(unittest.TestCase):
    """What the code sent back to the maker most often in job 1 round 1 is now said in the instructions up front."""

    def test_the_maker_reads_the_rules_its_round_1_broke(self):
        self.assertIn('add one question item for that question (content: "continued\n    from the previous page"', PAGE_HOW)
        self.assertIn("and make it their parent", PAGE_HOW)
        self.assertIn("no answer that only\n    repeats its question or the item's words", PAGE_HOW)
        self.assertIn('never "none": a concept of practice or PYQ questions takes\n  the type of what its questions test', CONNECT_HOW)
        self.assertIn("link the\n  question item, never its answer options", CONNECT_HOW)
        course = Course("10. Tissues and Its Types", "Science and Technology", "UPSC aspirants", "UPSC", "Hinglish")
        maker, _ = page_prefixes(course, rulebook.load())
        self.assertIn(PAGE_HOW, maker.text)

    def test_a_continued_question_from_the_previous_page_passes(self):
        passed = regression.load(TISSUE)                 # page 14 of job 1, round 2: the options name a "continued" question
        items = {i["item_id"]: i for i in passed["pages"][13]["value"]["items"]}
        self.assertEqual({items[i]["parent_item_id"] for i in ("i1", "i2", "i3", "i4")}, {"i20"})
        self.assertEqual(items["i20"]["kind"], "question")
        self.assertEqual([p for p in regression.check(passed) if p.startswith("page 14")], [])


class CheaperCheckerInput(unittest.TestCase):
    """Job 1: the checker read every answer with a space after each comma and colon (16.7% of those tokens, o200k)."""

    def test_the_checker_reads_compact_json(self):
        from bie.brain.pages import Page
        from bie.brain.understanding import page_step
        course = Course("10. Tissues and Its Types", "Science and Technology", "UPSC aspirants", "UPSC", "Hinglish")
        step = page_step(course, Page(5, blocks("Types:", "a. Skeletal"), b"\x89PNG" + b"7" * 40), page_count=14,
                         rulebook=rulebook.load())
        value = {"notes": {"about": "x"}, "page_summary": "Muscle: three kinds", "items": [{"item_id": "i1", "content": "a, b"}],
                 "boilerplate_block_ids": [], "text_image_disagreements": []}
        shown = step.review_user(value)[0]["text"].split("The understanding to review (JSON):\n", 1)[1]
        self.assertEqual(shown, '{"notes":{"about":"x"},"page_summary":"Muscle: three kinds","items":[{"item_id":"i1",'
                                '"content":"a, b"}],"boilerplate_block_ids":[],"text_image_disagreements":[]}')
        for name in ("bie/brain/understanding.py", "bie/brain/lesson.py"):          # the map, plan and script copies too
            source = (ROOT / name).read_text(encoding="utf-8")
            self.assertNotIn('to review (JSON):\\n" + json.dumps', source)
            self.assertEqual(source.count('to review (JSON):\\n" + cards.compact('), 2)


if __name__ == "__main__":
    unittest.main()
