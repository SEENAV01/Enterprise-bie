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

    def test_a_remake_shows_the_maker_its_answer_as_compact_json(self):
        import types
        from bie.brain.runner import SectionRunner, Step

        class Stub:
            def __init__(self, answers):
                self.answers, self.requests = list(answers), []

            def complete(self, route, request, prompt_version=None):
                self.requests.append(request)
                return types.SimpleNamespace(content=self.answers.pop(0), provenance={"via": "fake"}, model="stub",
                                             provider="stub", usage={"input_tokens": 1, "output_tokens": 1})

        stub = Stub([{"ok": False, "text": "a, b: c"}, {"ok": True, "text": ""}])
        step = Step(section="understand", unit="page-001", instructions_version="v", system="S", user="U", schema={},
                    check=lambda value: [] if value["ok"] else ["not ok"])
        result = SectionRunner(stub, maker="stub", reviewer=None, rulebook=rulebook.load()).run(step)
        self.assertEqual(result.status, "passed")
        self.assertEqual(stub.requests[1].messages[2], {"role": "assistant", "content": '{"ok":false,"text":"a, b: c"}'})


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


# ---------------------------------------------------------------- job 2 and Navin's decisions of 23 October 2026

def tiny_chapter(prerequisites=1):
    """Two book pages: page 1 has two teachable items (c1 and c2), page 2 one (c2); c1 is half a page, c2 one and a half."""
    def item(iid, page, teachable=True):
        return {"item_id": iid, "page": page, "kind": "paragraph", "parent_item_id": "", "source": "text", "block_ids": [],
                "content": "Cells form tissues.", "content_type": "definition", "teachable": teachable, "tests_item_ids": [],
                "teacher_understanding": [
                    {"depth": 1, "ask": "what", "question": "What?", "answer": "A group of cells.", "basis": "book"},
                    {"depth": 2, "ask": "why", "question": "Why?", "answer": "Division of labour.", "basis": "outside"}]}
    items = {"p001-i1": item("p001-i1", 1), "p001-i2": item("p001-i2", 1), "p002-i1": item("p002-i1", 2),
             "p002-i2": item("p002-i2", 2, teachable=False)}
    concepts = [{"concept_id": "c1", "name": "Tissue", "item_ids": ["p001-i1"], "content_type": "definition", "core_explanation": "x"},
                {"concept_id": "c2", "name": "Kinds", "item_ids": ["p001-i2", "p002-i1", "p002-i2"], "content_type": "definition",
                 "core_explanation": "x"}]
    pre = [{"name": f"Idea {n}", "why_needed": "x", "needed_for": ["c1"], "basis": "outside"} for n in range(1, prerequisites + 1)]
    return {"course": {"title": "T", "subject": "Biology", "learners": "UPSC", "exam": "UPSC", "language": "Hinglish"},
            "items": items, "map": {"concepts": concepts, "prerequisites_to_teach": pre, "teaching_order": ["c1", "c2"],
                                    "relations": [], "exam_focus": []}}


def plan_video(vid, cids, minutes, kind="topic", taught=(), note=""):
    return {"video_id": vid, "title": vid, "goal": "", "kind": kind, "concept_ids": list(cids), "prerequisites_taught": list(taught),
            "opening_hook": "", "story_or_analogy": "", "estimated_minutes": minutes, "length_note": note, "why_this_unit": ""}


def say_beat(bid, words, purpose="explain"):
    return {"beat_id": bid, "part_id": "", "purpose": purpose, "say": " ".join(["बात"] * words), "covers_item_ids": [], "answers": [],
            "on_screen": "", "basis": "book"}


class SimpleHindiAndBrackets(unittest.TestCase):
    """Job 2: 838 of about 880 round problems were everyday words flagged as hard, and the passed scripts carried 546
    needless brackets ("आम तौर (usually) पर"). Navin (23 October): brackets only on genuinely difficult words, never
    inside an idiom or a fixed phrase."""

    def test_word_forms_of_everyday_words_are_everyday(self):
        from bie.brain import hinglish
        simple = hinglish.load()
        for word in ("आता", "आते", "आएगा", "करवाना", "पड़ता", "बनावट", "मौजूद", "तय"):
            self.assertTrue(simple.is_simple(word), word)
        for word in ("सतह", "घर्षण", "सघन"):
            self.assertFalse(simple.is_simple(word), word)

    def test_code_removes_brackets_after_everyday_words_and_inside_fixed_phrases(self):
        from bie.brain import hinglish
        self.assertEqual(hinglish.clean("आम तौर (usually) पर cells छोटे होते हैं।"),
                         ("आम तौर पर cells छोटे होते हैं।", ["तौर (usually)"]))
        self.assertEqual(hinglish.clean("यह नहीं के बराबर (equal to) है।")[0], "यह नहीं के बराबर है।")
        self.assertEqual(hinglish.clean("मुख्य (main) बात")[0], "मुख्य बात")
        for kept in ("पत्ती की सतह (surface) देखिए।", "सही option (b) है।", "तो option कौन सा (a) है?"):
            self.assertEqual(hinglish.clean(kept), (kept, []))
        self.assertEqual(hinglish.difficult_words("आम तौर पर पत्ती की सतह गीली रहती है।"), ["सतह"])
        self.assertEqual(hinglish.bracket_problems("सही option (b) है।"), [])

    def test_the_script_step_tidies_brackets_before_the_checks_and_records_it(self):
        from bie.brain.lesson import tidy_script
        value = {"beats": [dict(say_beat("b1", 1), say="आम तौर (usually) पर ऐसा होता है।"), dict(say_beat("b2", 1), say="ठीक है।")]}
        tidy, changes = tidy_script(value)
        self.assertEqual(tidy["beats"][0]["say"], "आम तौर पर ऐसा होता है।")
        self.assertEqual(changes, {"brackets_removed": [{"beat_id": "b1", "removed": ["तौर (usually)"]}]})
        self.assertEqual(tidy_script({"beats": [value["beats"][1]]}), ({"beats": [value["beats"][1]]}, {}))

    def test_the_runner_records_what_code_normalized(self):
        import types
        from bie.brain.runner import SectionRunner, Step

        class Stub:
            def complete(self, route, request, prompt_version=None):
                return types.SimpleNamespace(content={"x": " a "}, provenance={"via": "fake"}, model="stub", provider="stub",
                                             usage={"input_tokens": 1, "output_tokens": 1})

        seen = []
        step = Step(section="lesson", unit="script-v1", instructions_version="v", system="S", user="U", schema={},
                    check=lambda value: seen.append(value) or [], normalize=lambda v: ({"x": v["x"].strip()}, {"stripped": 1}))
        result = SectionRunner(Stub(), maker="stub", reviewer=None, rulebook=rulebook.load()).run(step)
        self.assertEqual((result.status, result.output, seen), ("passed", {"x": "a"}, [{"x": "a"}]))
        self.assertEqual(result.rounds[0]["normalized"], {"stripped": 1})

    def test_patch_notes_keep_the_whole_units_notes(self):
        from bie.brain.runner import merge_notes
        first = {"about": "Tissue video", "key_questions": ["What is a tissue?"], "decisions": [{"decision": "a", "reason": "r"}],
                 "uncertain": ["x"]}
        patch = {"about": "local correction to beat b34", "key_questions": [], "decisions": [{"decision": "b", "reason": "r"}],
                 "uncertain": []}
        self.assertEqual(merge_notes(first, patch), {"about": "Tissue video", "key_questions": ["What is a tissue?"],
                                                     "decisions": first["decisions"] + patch["decisions"], "uncertain": []})
        self.assertEqual(merge_notes(None, patch), patch)


class NarrationTime(unittest.TestCase):
    """Job 2 spoke 458 minutes for 14 pages. Navin (23 October): 6-8 minutes of narration per book page, up to 25% more
    for a very dense video that says why; one 5-8 minute prerequisite video first; book content is never dropped."""

    def test_budgets_come_from_each_videos_share_of_the_pages(self):
        from bie.brain.lesson import book_pages, chapter_budget, concept_pages, video_budget
        chapter = tiny_chapter()
        self.assertEqual(book_pages(chapter), 2)
        self.assertEqual(concept_pages(chapter), {"c1": 0.5, "c2": 1.5})
        videos = [plan_video("v0", [], 6, "prerequisites", ["Idea 1"]), plan_video("v1", ["c1"], 4), plan_video("v2", ["c2"], 10)]
        self.assertEqual([video_budget(chapter, videos, v) for v in videos], [(5.0, 8.0), (3.0, 4.0), (9.0, 12.0)])
        self.assertEqual(chapter_budget(chapter, videos), (12.0, 16.0))
        dense = plan_video("v2", ["c2"], 14, note="Six terms on one page")
        self.assertEqual(video_budget(chapter, videos[:2] + [dense], dense), (9.0, 15.0))
        self.assertEqual(chapter_budget(chapter, videos[:2] + [dense]), (12.0, 19.0))

    def test_the_plan_needs_the_prerequisite_video_first_and_every_video_in_its_time(self):
        from bie.brain.lesson import check_plan, time_problems
        chapter = tiny_chapter()
        good = {"videos": [plan_video("v0", [], 6, "prerequisites", ["Idea 1"]), plan_video("v1", ["c1", "c2"], 14)]}
        self.assertEqual(check_plan(good, chapter), [])
        cases = {
            "no prerequisite video": ([plan_video("v1", ["c1", "c2"], 14)], "needs exactly one prerequisite video"),
            "not first": ([plan_video("v1", ["c1", "c2"], 14), plan_video("v0", [], 6, "prerequisites", ["Idea 1"])],
                          "the prerequisite video v0 comes first"),
            "a concept in it": ([plan_video("v0", ["c1"], 6, "prerequisites", ["Idea 1"]), plan_video("v1", ["c2"], 9)],
                                "its concept_ids are []"),
            "a name missing": ([plan_video("v0", [], 6, "prerequisites", []), plan_video("v1", ["c1", "c2"], 14)],
                               "prerequisites not taught: ['Idea 1']"),
            "taught in a topic video": ([plan_video("v0", [], 6, "prerequisites", ["Idea 1"]),
                                         plan_video("v1", ["c1", "c2"], 14, taught=["Idea 1"])], "prerequisites_taught is []"),
            "too long": ([plan_video("v0", [], 6, "prerequisites", ["Idea 1"]), plan_video("v1", ["c1", "c2"], 30)],
                         "30 minutes is outside its narration budget of 12.0-16.0"),
        }
        for name, (videos, fragment) in cases.items():
            with self.subTest(name):
                self.assertTrue(any(fragment in p for p in time_problems({"videos": videos}, chapter)), fragment)
        crowded = copy.deepcopy(chapter)                 # a third item on page 1: c1 is a third of a page, 2.0-2.7 minutes
        crowded["items"]["p001-i3"] = dict(crowded["items"]["p001-i2"], item_id="p001-i3")
        crowded["map"]["concepts"][1]["item_ids"].append("p001-i3")
        short = [plan_video("v0", [], 6, "prerequisites", ["Idea 1"]), plan_video("v1", ["c1"], 2), plan_video("v2", ["c2"], 12)]
        self.assertTrue(any("merge it with the video before or after" in p for p in time_problems({"videos": short}, crowded)))
        none = tiny_chapter(prerequisites=0)
        self.assertTrue(any("lists no prerequisites" in p for p in time_problems(good, none)))
        self.assertEqual(time_problems({"videos": [plan_video("v1", ["c1", "c2"], 14)]}, none), [])

    def test_a_dense_video_may_go_25_percent_over_only_with_its_reason(self):
        from bie.brain.lesson import time_problems
        chapter = tiny_chapter()
        long = lambda note: {"videos": [plan_video("v0", [], 6, "prerequisites", ["Idea 1"]), plan_video("v1", ["c1", "c2"], 19, note=note)]}
        self.assertTrue(time_problems(long(""), chapter))
        self.assertEqual(time_problems(long("Pages 1 and 2 hold eleven terms the exam asks."), chapter), [])

    def test_the_script_is_checked_by_its_spoken_words(self):
        from bie.brain.lesson import length_problems, spoken_minutes
        topic = plan_video("v1", ["c1"], 4)
        self.assertEqual(spoken_minutes([say_beat("b1", 260)]), 2.0)
        self.assertEqual(length_problems([say_beat("b1", 455)], topic, (3.0, 4.0)), [])            # 3.5 minutes
        self.assertIn("speaks about 4.5 minutes", length_problems([say_beat("b1", 585)], topic, (3.0, 4.0))[0])
        self.assertIn("speaks only about 2.0 minutes", length_problems([say_beat("b1", 260)], topic, (3.0, 4.0))[0])
        self.assertEqual(length_problems([say_beat("b1", 340)], topic, (3.0, 4.0)), [])            # 2.6 >= 0.85 x 3
        reminders = [say_beat(f"b{n}", 400 if n == 1 else 5, "prerequisite") for n in range(1, 4)]
        self.assertIn("at most 2 beats", length_problems(reminders, topic, (3.0, 4.0))[0])
        first = plan_video("v0", [], 6, "prerequisites", ["Idea 1"])
        self.assertEqual(length_problems([say_beat("b1", 780, "prerequisite")] * 1, first, (5.0, 8.0)), [])

    def test_the_prerequisite_video_has_one_part_per_prerequisite(self):
        from bie.brain.lesson import chapter_naksha, script_card, script_prefixes, video_budget, _script_source
        chapter = tiny_chapter(prerequisites=2)
        plan = {"videos": [plan_video("v0", [], 6, "prerequisites", ["Idea 1", "Idea 2"]), plan_video("v1", ["c1", "c2"], 14)]}
        book = rulebook.load()
        course = Course(**chapter["course"])
        card = script_card(course, chapter, chapter_naksha(chapter), plan, plan["videos"][0], rulebook=book,
                           prefix=script_prefixes(course, book)[0])
        self.assertEqual([p["part_id"] for p in card["parts"]], ["pre1", "pre2"])
        self.assertEqual(card["coverage"]["must_cover"], ["pre1", "pre2"])
        source = _script_source(chapter, plan["videos"][0], video_budget(chapter, plan["videos"], plan["videos"][0]))
        self.assertIn("Narration time (S2-01): 5.0-8.0 minutes, about 650-1040 spoken words", source)
        self.assertIn("pre2 | Idea 2", source)

    def test_only_questions_answered_from_the_book_are_required(self):
        from bie.brain.lesson import book_questions
        chapter = tiny_chapter()
        self.assertEqual(book_questions(chapter, ["p001-i1#q1", "p001-i1#q2", "p002-i1#q1"]), ["p001-i1#q1", "p002-i1#q1"])


class PrerequisiteTrim(unittest.TestCase):
    """Job 1's map listed 30 prerequisites, most of them background to other prerequisites. Navin (23 October): only what
    the chapter directly needs, never a chain; more than 8 needs a reason (a warning, not a cap); an older map is trimmed
    once before its lesson is planned."""

    def setUp(self):
        from bie.brain.understanding import quality
        passed = regression.load(TISSUE)
        self.chapter = {"course": passed["course"], "items": passed["map"]["items"], "map": passed["map"]["map"],
                        "source_sha256": passed["source_sha256"], "pages": [], "maker_route": "codex", "reviewer_route": "google",
                        "rulebook_version": "2026-10-21.9", "map_status": "passed", "cost_usd": 0.0}
        self.chapter["quality"] = quality(self.chapter)        # a chapter_map.json as job 1 wrote it, without its pages

    def test_job_1s_map_needs_the_trim_and_the_rule_change_is_visible(self):
        from bie.brain.prerequisites import needs_trim
        self.assertTrue(needs_trim(self.chapter))
        changed = regression.changed_rule_problems(regression.load(TISSUE))
        self.assertEqual([(p.split(";")[0], c["rule"]) for p, c in changed],
                         [("map: prerequisites_to_teach has 30 prerequisites", "S1-12")])
        newer = dict(regression.load(TISSUE), rulebook="2026-10-21.10")      # a set made under the new rule gets no waiver
        self.assertEqual(len(regression.check(newer)), 1)

    def test_the_trim_check_wants_every_current_prerequisite_kept_merged_or_dropped_once(self):
        from bie.brain.prerequisites import check_trim, current
        ids = [pid for pid, _ in current(self.chapter)]
        self.assertEqual(len(ids), 30)
        keep = lambda from_ids: {"name": "Cell", "why_needed": "x", "needed_for": ["c01"], "basis": "outside", "from_ids": from_ids}
        good = {"prerequisites": [keep(ids[:2])], "dropped": [{"id": i, "reason": "background"} for i in ids[2:]]}
        self.assertEqual(check_trim(good, self.chapter), [])
        bad = {"prerequisites": [keep(ids[:2]), keep([ids[1], "pre99"])] + [dict(keep([]), name=f"P{n}") for n in range(8)],
               "dropped": [{"id": i, "reason": "x"} for i in ids[3:]]}
        problems = check_trim(bad, self.chapter)
        for fragment in ("has 10 prerequisites", "'cell' is listed more than once", "pre2 must be in exactly one kept",
                         "pre3 must be in exactly one kept prerequisite's from_ids or in dropped (it is in 0)",
                         "unknown prerequisite ids ['pre99']", "from_ids must name the current prerequisites"):
            self.assertTrue(any(fragment in p for p in problems), fragment)

    def test_more_than_8_is_a_warning_the_maker_answers_never_a_cap(self):
        # Navin, 23 October 2026: "only what is directly needed, no chains", not a number.
        from bie.brain.prerequisites import check_trim, current
        from bie.brain.understanding import prerequisite_problems, render_markdown
        ids = [pid for pid, _ in current(self.chapter)]
        keep = [{"name": f"P{n}", "why_needed": "x", "needed_for": ["c01"], "basis": "outside", "from_ids": [ids[n]]}
                for n in range(10)]
        dropped = [{"id": i, "reason": "background"} for i in ids[10:]]
        without = check_trim({"prerequisites": keep, "dropped": dropped, "prerequisite_note": ""}, self.chapter)
        self.assertTrue(any("has 10 prerequisites" in p and "prerequisite_note" in p for p in without))
        note = "Each of the ten is used directly by a chapter concept; none is background to another."
        self.assertEqual(check_trim({"prerequisites": keep, "dropped": dropped, "prerequisite_note": note}, self.chapter), [])
        self.assertEqual(prerequisite_problems(keep, {"c01"}, note), [])
        chapter = copy.deepcopy(self.chapter)
        chapter["map"]["prerequisites_to_teach"], chapter["map"]["prerequisite_note"] = keep, note
        self.assertIn("More than 8 prerequisites (warning, S1-12): " + note, render_markdown(chapter))

    def test_the_trim_runs_once_and_its_map_passes_todays_checks(self):
        from bie.brain.prerequisites import needs_trim, run_trim
        from bie.brain.understanding import check_connect
        from bie.model_gateway.claude_adapter import ClaudeAdapter
        from bie.model_gateway.gpt_adapter import GPTAdapter
        from bie.model_gateway.live.gateway import LiveGateway
        from bie.brain.fake import BrainFakeClient
        from bie.brain.runner import SectionRunner
        maker, reviewer = BrainFakeClient("anthropic"), BrainFakeClient("openai")
        gateway = LiveGateway({"anthropic": ClaudeAdapter(maker, "fake-claude"), "openai": GPTAdapter(reviewer, "fake-gpt")},
                              sleep=lambda s: None)
        course = Course(**self.chapter["course"])
        with tempfile.TemporaryDirectory() as folder:
            runner = SectionRunner(gateway, maker="anthropic", reviewer="openai", rulebook=rulebook.load(),
                                   records_dir=Path(folder, "records"))
            trimmed, summary = run_trim(self.chapter, course, runner, folder)
            self.assertEqual((summary["status"], summary["before"], summary["after"]), ("passed", 30, 8))
            self.assertFalse(needs_trim(trimmed))
            self.assertEqual(check_connect(trimmed["map"], trimmed["items"]), [])
            self.assertEqual(trimmed["map"]["concepts"], self.chapter["map"]["concepts"])          # nothing else changes
            self.assertEqual(len(trimmed["prerequisite_trim"]["dropped"]), 22)
            saved = json.loads(Path(folder, "chapter_map.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["naksha"]["sha256"], json.loads(Path(folder, "naksha.json").read_text(encoding="utf-8"))["sha256"])
            self.assertIn("Trimmed from 30 to 8 prerequisites", Path(folder, "MAP.md").read_text(encoding="utf-8"))
            calls = len(maker.calls)
            again, summary = run_trim(trimmed, course, runner, folder)
            self.assertEqual((summary["status"], len(maker.calls)), ("not needed", calls))
            self.assertIs(again, trimmed)

    def test_a_lesson_run_trims_an_old_map_first_and_plans_the_prerequisite_video(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder, "chapter_map.json")
            path.write_text(json.dumps(self.chapter, ensure_ascii=False), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                code = run_brain.main(["--fake", "--section", "lesson", "--chapter-map", str(path), "--out", str(Path(folder, "run")),
                                       "--workers", "1", "--max-inr", "100000"])
            self.assertEqual(code, 0)
            summary = json.loads(Path(folder, "run", "SUMMARY.json").read_text(encoding="utf-8"))
            self.assertEqual({k: summary["prerequisite_trim"][k] for k in ("status", "before", "after")},
                             {"status": "passed", "before": 30, "after": 8})
            lesson = json.loads(Path(folder, "run", "lesson_plan.json").read_text(encoding="utf-8"))
            first = lesson["plan"]["videos"][0]
            self.assertEqual((first["video_id"], first["kind"], len(first["prerequisites_taught"])), ("v0", "prerequisites", 8))
            self.assertEqual(lesson["quality"]["videos_passed"], lesson["quality"]["videos"])
            low, high = lesson["quality"]["budget_minutes"]["topic_videos"]
            spoken = sum(v["spoken_minutes"] for v in lesson["videos"] if v["kind"] == "topic")
            self.assertTrue(low <= spoken <= high, (low, spoken, high))
            self.assertTrue(Path(folder, "run", "scripts", "v0.md").exists())

    def test_the_trim_card_belongs_to_the_connect_section(self):
        from bie.brain import cards
        from bie.brain.prerequisites import trim_step
        step = trim_step(Course(**self.chapter["course"]), self.chapter, rulebook=rulebook.load())
        self.assertEqual((step.card["section"], step.card["task"]), ("connect", "trim_prerequisites"))
        self.assertIn("trim_prerequisites", cards.SECTION_TASKS["connect"])
        self.assertEqual(len(step.card["coverage"]["must_cover"]), 30)
        self.assertIn("never drop one the chapter directly needs to reach a number", step.system)
        self.assertIn("prerequisite_note", step.system)


class Section1RulesOfNavin(unittest.TestCase):
    def test_typos_stay_as_printed_and_one_answer_has_one_basis(self):
        book = rulebook.load()
        rules = {r.id: r.rule for r in book.rules}
        self.assertIn("Cartiage [Cartilage]", rules["S1-13"])
        self.assertIn("two answers", rules["S1-14"])
        self.assertIn("Cartiage [Cartilage]", PAGE_HOW)
        self.assertIn("S1-14", PAGE_HOW)
        self.assertIn("never drop a prerequisite the chapter directly needs to stay under 8", CONNECT_HOW)
        self.assertIn("a warning, not a limit", CONNECT_HOW)
        self.assertIn("the rule is not a number", rules["S1-12"])
        self.assertIn("6-8 minutes per book page", rules["S2-01"])


class CacheProbe(unittest.TestCase):
    """Every Gemini call of jobs 1 and 2 reported 0 cached input tokens. Navin (23 October): yes to a ~Rs 1 probe."""

    def test_the_probe_runs_two_calls_with_one_long_prefix_under_a_small_cap(self):
        import run_blind_test
        system, stable = run_blind_test.cache_probe_prefix()
        self.assertGreater(len(system) + len(stable), 15000)          # about 4,300 tokens: above the 4,096-token minimum
        with tempfile.TemporaryDirectory() as folder:
            code, out = quiet(run_blind_test.main, ["--mode", "cache-probe", "--fake", "--providers", "google", "--out", folder])
            self.assertEqual(code, 0)
            summary = json.loads(Path(folder, "SUMMARY.json").read_text(encoding="utf-8"))
            calls = summary["cache_probe"]["google"]["calls"]
            self.assertEqual([c["call"] for c in calls], [1, 2])
            self.assertFalse(summary["cache_probe"]["google"]["cache_hit"])        # the fake reports no cached tokens
            rows = [json.loads(line) for line in Path(folder, "LEDGER.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual([r["request_id"] for r in rows], ["cache-probe:google:1", "cache-probe:google:2"])
            with self.assertRaises(SystemExit):
                run_blind_test.main(["--mode", "cache-probe", "--fake", "--providers", "google", "--out", folder, "--max-inr", "50"])

    def test_the_compat_client_keeps_the_gateways_own_usage_fields(self):
        from bie.model_gateway.live.compat_client import OpenAICompatChatClient
        client = OpenAICompatChatClient("sk-test-key")
        parsed = client.parse({"model": "google/gemini-4-argon", "choices": [{"message": {"content": "{}"}, "finish_reason": "stop"}],
                               "usage": {"prompt_tokens": 4300, "completion_tokens": 20, "cost": 0.85,
                                         "prompt_tokens_details": {"cached_tokens": 2048}}})
        self.assertEqual(parsed["usage"]["cached_input_tokens"], 2048)
        self.assertEqual(client.last_usage_raw["cost"], 0.85)

    def test_the_lesson_estimate_uses_job_2s_measured_cost(self):
        from bie.brain import cost
        est = cost.estimate("lesson", 14, rate=94.59, maker_model="gpt-6.1-sol", reviewer_model="google/gemini-4-argon",
                            maker_subscription=True)
        self.assertEqual(est["sections"]["lesson"]["basis"], "measured")
        self.assertAlmostEqual(est["total_inr"], 104.48, delta=0.5)       # job 2's ledger: Rs 104.48 for the lesson


class ScriptReviewerFollowsTheTimeRule(unittest.TestCase):
    """Job 3 (t045c, 23 October): 5 of 11 scripts failed in the same loop. Round 2 cut the script into its time, the
    reviewer blocked it for leaving out teacher questions answered from outside the book (optional under S2-02) and
    counted the words itself (1,105 against BIE's 1,586), round 3 added them back and the script was too long again."""

    def chapter_and_step(self):
        from bie.brain.lesson import script_step
        chapter = tiny_chapter()
        plan = {"videos": [plan_video("v0", [], 6, "prerequisites", ["Idea 1"]), plan_video("v1", ["c1", "c2"], 14)]}
        return chapter, plan, script_step(Course(**chapter["course"]), chapter, plan, plan["videos"][1], rulebook=rulebook.load())

    def test_the_reviewer_requires_only_book_questions_and_never_counts_words(self):
        _, _, step = self.chapter_and_step()
        self.assertIn('A teacher question whose basis is "outside" is optional', step.review_system)
        self.assertIn("Never count words or judge the length yourself", step.review_system)
        self.assertIn("bie.brain.lesson-script-review/3", step.review_system)
        shown = step.review_user({"beats": [say_beat("b1", 260)], "parts": [], "title": "t", "notes": None})[0]["text"]
        self.assertIn("BIE's code measured: 2.0 spoken minutes; narration time 12.0-16.0 minutes", shown)

    def test_a_patch_round_tells_the_maker_its_measured_time(self):
        _, _, step = self.chapter_and_step()
        hint = step.patch_hint({"beats": [say_beat("b1", 1950)]})
        self.assertIn("measured this script at 15.0 spoken minutes; the video's narration time is 12.0-16.0 minutes", hint)
        self.assertIn("pay for every addition with a cut", hint)

    def test_the_runner_accepts_a_patch_hint_made_from_the_answer(self):
        import types
        from bie.brain.runner import SectionRunner, Step

        class Stub:
            def __init__(self):
                self.answers, self.requests = [{"ok": False}, {"ok": True}], []

            def complete(self, route, request, prompt_version=None):
                self.requests.append(request)
                return types.SimpleNamespace(content=self.answers.pop(0), provenance={"via": "fake"}, model="stub",
                                             provider="stub", usage={"input_tokens": 1, "output_tokens": 1})

        stub = Stub()
        step = Step(section="lesson", unit="script-v1", instructions_version="v", system="S", user="U", schema={},
                    check=lambda value: [] if value["ok"] else ["not ok"], patch_schema={}, apply_patch=lambda old, patch: patch,
                    patch_hint=lambda value: f"HINT ok={value['ok']}")
        self.assertEqual(SectionRunner(stub, maker="stub", reviewer=None, rulebook=rulebook.load()).run(step).status, "passed")
        self.assertIn("HINT ok=False", stub.requests[1].messages[3]["content"])

    def test_a_pattern_step_for_when_there_is_one_is_optional(self):
        from bie.brain.lesson import frame_problems
        types_ = ct.load()
        card = {"parts": [{"part_id": "c1.1", "type": "facts_numbers", "item_ids": ["p001-i1"]}]}
        frame = {k: "x" for k in ("process", "how", "when", "conditions", "atmosphere")}
        beats = lambda steps: {"parts": [{"part_id": "c1.1", "frame": frame}],
                               "beats": [dict(say_beat(f"b{n}", 5), part_id="c1.1", step=n) for n in steps]}
        self.assertIn("formula", types_.pattern("facts_numbers")[4])
        self.assertEqual(frame_problems(beats([1, 2, 3, 4]), card, types_)[0], [])
        self.assertTrue(any("4) what it changes or proves" in p for p in frame_problems(beats([1, 2, 3]), card, types_)[0]))

    def test_everyday_words_from_job_3_are_simple_and_formal_ones_are_not(self):
        from bie.brain import hinglish
        simple = hinglish.load()
        for word in ("पड़ोसी", "मर्ज़ी", "गुजरते", "सटकर", "झड़ने", "किस्में", "संभव", "समूह"):
            self.assertTrue(simple.is_simple(word), word)
        for word in ("पदार्थ", "प्रभावित", "मुख्यतः", "नियंत्रित", "निष्कर्ष"):
            self.assertFalse(simple.is_simple(word), word)

    def test_the_maker_reads_the_beat_load_limit_up_front(self):
        from bie.brain.lesson import script_prefixes
        maker = script_prefixes(Course(**tiny_chapter()["course"]), rulebook.load())[0]
        self.assertIn("at most about 70 spoken words with one new item, 50 with two and 30 with three", maker.text)


class PatchesKeepEveryPatternStep(unittest.TestCase):
    """Job 3 resumed (t045c resume): 4 of the 5 failed scripts passed with no blocking review finding; v9 failed by 0.1
    minute because two patches cut beats that were the only beat of a pattern step (its recaps) to save time."""

    def test_sole_step_beats_are_named_in_the_patch_hint(self):
        from bie.brain.lesson import script_step, sole_step_beats
        beats = [dict(say_beat("b1", 5), part_id="c1.1", step=1), dict(say_beat("b2", 5), part_id="c1.1", step=2),
                 dict(say_beat("b3", 5), part_id="c1.1", step=2), dict(say_beat("b4", 5), part_id="", step=0)]
        self.assertEqual(sole_step_beats(beats), ["b1"])
        chapter = tiny_chapter()
        plan = {"videos": [plan_video("v0", [], 6, "prerequisites", ["Idea 1"]), plan_video("v1", ["c1", "c2"], 14)]}
        step = script_step(Course(**chapter["course"]), chapter, plan, plan["videos"][1], rulebook=rulebook.load())
        hint = step.patch_hint({"beats": beats})
        self.assertIn("Never remove beats b1: each is the only beat of a teaching-pattern step", hint)
        self.assertNotIn("Never remove", step.patch_hint({"beats": beats[3:]}))       # a hook beat has no step

    def test_words_from_the_resumed_run(self):
        from bie.brain import hinglish
        simple = hinglish.load()
        for word in ("पड़ोस", "बेवजह", "मुताबिक", "राहों"):
            self.assertTrue(simple.is_simple(word), word)
        for word in ("अतिरिक्त", "भ्रम"):
            self.assertFalse(simple.is_simple(word), word)


if __name__ == "__main__":
    unittest.main()
