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
import os
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


class LeanCodexCalls(unittest.TestCase):
    """Job 1: every Codex call carried Codex's own agent instructions and tools (14,208 tokens for a one-line preflight)."""

    def call(self):
        from bie.model_gateway.live.codex_client import CodexExecClient
        with tempfile.TemporaryDirectory() as state:
            environment = dict(os.environ, BIE_FAKE_CODEX_STATE=state, BIE_FAKE_CODEX_MODE="ok")
            client = CodexExecClient(executable=f"{sys.executable} {ROOT / 'bie' / 'brain' / 'fake_codex.py'}", env=environment)
            content = [{"type": "text", "text": "Set status to ready."},
                       {"type": "image", "media_type": "image/png", "data": "iVBORw0KGgo="}]
            schema = {"type": "object", "additionalProperties": False, "required": ["status"],
                      "properties": {"status": {"type": "string", "enum": ["ready"]}}}
            raw = client.responses_create(model="gpt-6.1-sol", messages=[{"role": "system", "content": "Be exact."},
                                                                         {"role": "user", "content": content}],
                                          response_schema=schema)
            self.assertEqual(json.loads(raw["content"]), {"status": "ready"})
            return json.loads(Path(state, "calls.jsonl").read_text().splitlines()[0])

    def test_a_lean_call_replaces_codex_instructions_and_switches_tools_off(self):
        from bie.model_gateway.live import codex_client as cc
        call = self.call()
        self.assertEqual(call["instructions"], cc.LEAN_INSTRUCTIONS)
        self.assertIn("--strict-config", call["args"])              # a renamed setting stops codex before any request
        self.assertTrue(set(cc.LEAN_SETTINGS) <= set(call["settings"]))
        self.assertEqual(call["disabled"], list(cc.LEAN_FEATURES_OFF))
        self.assertTrue({"shell_tool", "unified_exec", "browser_use", "computer_use", "apps"} <= set(call["disabled"]))
        self.assertEqual(call["args"][-2:], ["--", "-"])          # the prompt on stdin is never read as an image file
        self.assertEqual((call["images"], call["images_exist"]), ([".png"], True))
        self.assertGreater(call["prompt_chars"], 0)

    def test_lean_calls_can_be_switched_off(self):
        from unittest import mock
        with mock.patch.dict(os.environ, {"BIE_CODEX_LEAN": "0"}):
            call = self.call()
        self.assertIsNone(call["instructions"])
        self.assertEqual(call["disabled"], [])
        self.assertNotIn("--strict-config", call["args"])
        self.assertEqual(call["args"][-2:], ["--", "-"])


class MeasuredTheSameWay(unittest.TestCase):
    """Every seekh change is measured before and after with one tool, from the run folders' records."""

    @staticmethod
    def folder(root, name, rate, records):
        Path(root, name, "records").mkdir(parents=True)
        Path(root, name, "SUMMARY.json").write_text(json.dumps({"cost": {"usd_inr": rate}}), encoding="utf-8")
        for file, record in records.items():
            Path(root, name, "records", file).write_text(json.dumps(record), encoding="utf-8")
        return Path(root, name)

    def test_first_try_rounds_tokens_rupees_and_round_one_problems(self):
        import seekh_measure
        maker = {"input_tokens": 100, "output_tokens": 40}
        page = {"section": "understand", "unit": "page-001", "status": "passed", "cost_usd": 0.01, "seconds": 120, "rounds": [
            {"maker": maker, "code_problems": ["[code] item i3: an answer_option needs its question as parent_item_id"]},
            {"maker": maker, "review": {"input_tokens": 50, "output_tokens": 5,
                                        "value": {"wrong": [{"severity": "minor"}], "missing": [], "shallow": []}}}]}
        stopped = {"section": "connect", "unit": "chapter", "status": "stopped", "cost_usd": 0.0, "seconds": 30, "rounds": [
            {"maker": maker, "code_problems": ["[code] concept c34: give it its main content type, not 'none'"]}]}
        passed = {"section": "connect", "unit": "chapter", "status": "passed", "cost_usd": 0.02, "seconds": 60, "rounds": [
            {"maker": maker, "code_problems": [], "review": {"input_tokens": 80, "output_tokens": 8, "value": {"problems": []}}}]}
        with tempfile.TemporaryDirectory() as root:
            first = self.folder(root, "first", 100.0, {"understand--page-001.json": page, "connect--chapter.json": stopped})
            later = self.folder(root, "later", 90.0, {"connect--chapter.json": passed})
            got = seekh_measure.measure([first, later])
            self.assertEqual(list(got), ["pages", "map"])
            pages, chapter_map = got["pages"], got["map"]
            self.assertEqual((pages["passed"], pages["first_try"], pages["rounds_per_unit"]), (1, 0, 2.0))
            self.assertEqual((pages["maker_tokens_per_unit"], pages["checker_tokens_per_unit"]), ([200, 80], [50, 5]))
            self.assertEqual((pages["inr_per_unit"], pages["minutes_per_unit"]), (1.0, 2.0))
            self.assertEqual(pages["round_one_code_problems"], {"item _: an answer_option needs its question as parent_item_id": 1})
            self.assertEqual(pages["reviewer_findings"], {"minor": 1})
            self.assertEqual((chapter_map["first_try"], chapter_map["inr_total"]), (1, 1.8))     # the later run's map replaced it
            code, text = quiet(seekh_measure.main, [str(first), str(later)])
            self.assertEqual(code, 0)
            self.assertIn("| First-try pass | 0 of 1 (0%) | 1 of 1 (100%) |", text)
            with self.assertRaises(SystemExit):
                seekh_measure.main([str(Path(root, "missing"))])


if __name__ == "__main__":
    unittest.main()
