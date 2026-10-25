"""Task 039: image parts in the gateway, the vision rulebook, the section runner and Section 1 (offline)."""
from __future__ import annotations

import base64
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests" / "productization" / "document_intelligence"))

from bie.brain import rulebook
from bie.brain.fake import BrainFakeClient
from bie.brain.pages import Block, Page, parse_page_range
from bie.brain.runner import SectionRunner, Step, safe_content
from bie.brain.understanding import (Course, _chapter_items, check_connect, check_page, review_problems, run_chapter)
from bie.model_gateway.claude_adapter import ClaudeAdapter
from bie.model_gateway.gpt_adapter import GPTAdapter
from bie.model_gateway.live.anthropic_client import AnthropicClient
from bie.model_gateway.live.compat_client import OpenAICompatChatClient
from bie.model_gateway.live.config import make_client
from bie.model_gateway.live.errors import ProviderError
from bie.model_gateway.live.gateway import LiveGateway
from bie.model_gateway.live.gemini_client import GeminiClient
from bie.model_gateway.live.messages import split_messages, text_of
from bie.model_gateway.live.openai_client import OpenAIClient

PNG = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"0" * 64).decode()
IMAGE = {"type": "image", "media_type": "image/png", "data": PNG}
PARTS = [{"type": "text", "text": "Read this page."}, IMAGE]
MESSAGES = ({"role": "system", "content": "Be exact."}, {"role": "user", "content": PARTS})
COURSE = Course("Test chapter", "Biology", "UPSC aspirants", "UPSC", "Hinglish")


class StubTransport:
    def __init__(self, reply):
        self.reply = reply
        self.bodies = []

    def request_json(self, method, url, headers, body=None, *, provider, secrets=()):
        self.bodies.append(body)
        return self.reply


class ImageParts(unittest.TestCase):
    def test_split_messages_keeps_parts(self):
        system, conversation = split_messages(MESSAGES, provider="t")
        self.assertEqual(system, "Be exact.")
        self.assertEqual(conversation[0]["content"], PARTS)
        self.assertEqual(text_of(PARTS), "Read this page.")

    def test_rejects_images_outside_user_turns_and_bad_parts(self):
        bad = [
            ({"role": "system", "content": PARTS}, {"role": "user", "content": "x"}),
            ({"role": "user", "content": "x"}, {"role": "assistant", "content": [IMAGE]}),
            ({"role": "user", "content": [{"type": "image", "media_type": "image/png", "data": "not base64!"}]},),
            ({"role": "user", "content": [{"type": "image", "media_type": "image/gif", "data": PNG}]},),
            ({"role": "user", "content": [{"type": "video", "data": PNG}]},),
            ({"role": "user", "content": []},),
        ]
        for messages in bad:
            with self.subTest(messages=str(messages)[:80]), self.assertRaises(ProviderError):
                split_messages(messages, provider="t")

    def test_anthropic_body(self):
        transport = StubTransport({"content": [{"type": "text", "text": "{}"}], "stop_reason": "end_turn", "usage": {}})
        AnthropicClient("k", transport=transport).messages_create(model="m", messages=MESSAGES)
        content = transport.bodies[0]["messages"][0]["content"]
        self.assertEqual(content[0], {"type": "text", "text": "Read this page."})
        self.assertEqual(content[1], {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": PNG}})

    def test_openai_body(self):
        reply = {"status": "completed", "output": [{"type": "message", "content": [{"type": "output_text", "text": "{}"}]}]}
        transport = StubTransport(reply)
        OpenAIClient("k", transport=transport).responses_create(model="m", messages=MESSAGES)
        content = transport.bodies[0]["input"][0]["content"]
        self.assertEqual(content[0], {"type": "input_text", "text": "Read this page."})
        self.assertEqual(content[1], {"type": "input_image", "image_url": "data:image/png;base64," + PNG})

    def test_gemini_body(self):
        reply = {"candidates": [{"content": {"parts": [{"text": "{}"}]}, "finishReason": "STOP"}]}
        transport = StubTransport(reply)
        GeminiClient("k", transport=transport).generate(model="m", messages=MESSAGES)
        parts = transport.bodies[0]["contents"][0]["parts"]
        self.assertEqual(parts, [{"text": "Read this page."}, {"inlineData": {"mimeType": "image/png", "data": PNG}}])

    def test_compat_body(self):
        reply = {"choices": [{"message": {"content": "{}"}, "finish_reason": "stop"}]}
        transport = StubTransport(reply)
        OpenAICompatChatClient("k", transport=transport).chat(model="m", messages=MESSAGES)
        content = transport.bodies[0]["messages"][1]["content"]
        self.assertEqual(content[1], {"type": "image_url", "image_url": {"url": "data:image/png;base64," + PNG}})

    def test_plain_text_messages_unchanged(self):
        plain = ({"role": "system", "content": "s"}, {"role": "user", "content": "hello"})
        transport = StubTransport({"content": [{"type": "text", "text": "{}"}], "stop_reason": "end_turn", "usage": {}})
        AnthropicClient("k", transport=transport).messages_create(model="m", messages=plain)
        self.assertEqual(transport.bodies[0]["messages"], [{"role": "user", "content": "hello"}])

    def test_output_cap(self):
        self.assertEqual(make_client("anthropic", "k", max_output_tokens=32000).max_tokens, 32000)
        self.assertEqual(make_client("openai", "k", max_output_tokens=32000).max_output_tokens, 32000)
        self.assertEqual(make_client("google", "k", max_output_tokens=32000).max_output_tokens, 32000)
        self.assertEqual(make_client("anthropic", "k", via="aicredits", max_output_tokens=32000).max_tokens, 32000)
        self.assertEqual(make_client("anthropic", "k").max_tokens, AnthropicClient("k").max_tokens)


class Rulebook(unittest.TestCase):
    def test_the_vision_rulebook_loads(self):
        book = rulebook.load()
        self.assertIn("vision-2026-10-21@", book.version)
        ids = [r.id for r in book.for_section("understand")]
        for wanted in ("G-01", "G-02", "G-03", "S1-01", "S1-03", "S1-04", "S1-06", "S1-11"):
            self.assertIn(wanted, ids)
        self.assertNotIn("S6-01", ids)
        self.assertIn("S1-12", [r.id for r in book.for_section("connect")])
        self.assertNotIn("R-01", [rule_id for rule_id, _ in book.checklist("review")])
        self.assertIn("[S1-03]", book.instructions("understand"))
        self.assertTrue(book.reviewer_instructions().startswith("[R-01]"))

    def _write(self, folder, rules, version="1"):
        Path(folder, "book.json").write_text(json.dumps({"version": version, "rules": rules}), encoding="utf-8")

    def test_only_locked_rules_are_used_and_bad_files_fail(self):
        base = {"sections": ["understand"], "rule": "r", "check": "c?"}
        with tempfile.TemporaryDirectory() as folder:
            self._write(folder, [dict(base, id="A", status="locked"), dict(base, id="B", status="proposed")])
            self.assertEqual([r.id for r in rulebook.load(folder).for_section("understand")], ["A"])
            self._write(folder, [dict(base, id="A", status="locked"), dict(base, id="A", status="locked")])
            with self.assertRaises(rulebook.RulebookError):
                rulebook.load(folder)
            self._write(folder, [dict(base, id="A", status="maybe")])
            with self.assertRaises(rulebook.RulebookError):
                rulebook.load(folder)
            self._write(folder, [{"id": "A", "status": "locked"}])
            with self.assertRaises(rulebook.RulebookError):
                rulebook.load(folder)

    def test_a_changed_rule_changes_the_digest(self):
        base = {"id": "A", "sections": ["*"], "status": "locked", "check": "c?"}
        with tempfile.TemporaryDirectory() as folder:
            self._write(folder, [dict(base, rule="one")])
            first = rulebook.load(folder).digest
            self._write(folder, [dict(base, rule="two")])
            self.assertNotEqual(first, rulebook.load(folder).digest)


SIMPLE_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["notes", "items"],
                 "properties": {"notes": {"type": "object"}, "items": {"type": "array", "items": {"type": "object"}}}}
REVIEW_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["verdict", "missing"],
                 "properties": {"verdict": {"type": "string"}, "missing": {"type": "array"}}}


def gateway(maker_client=None, reviewer_client=None):
    routes = {"anthropic": ClaudeAdapter(maker_client or BrainFakeClient("anthropic"), "fake-a"),
              "openai": GPTAdapter(reviewer_client or BrainFakeClient("openai"), "fake-o")}
    return LiveGateway(routes, sleep=lambda s: None)


def page_with(blocks=(("p0001-b0001", "Cells form tissues."),), image=True):
    return Page(1, tuple(Block(i, t, (0, 0, 1, 1)) for i, t in blocks), b"\x89PNG" + b"1" * 40 if image else None)


class Runner(unittest.TestCase):
    def setUp(self):
        self.book = rulebook.load()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def step(self, page, check=None):
        from bie.brain.understanding import page_step
        step = page_step(COURSE, page, page_count=1, rulebook=self.book)
        if check is not None:
            step.check = check
        return step

    def test_pass_in_one_round_writes_a_record_without_image_data(self):
        runner = SectionRunner(gateway(), maker="anthropic", reviewer="openai", rulebook=self.book, records_dir=self.tmp.name)
        result = runner.run(self.step(page_with()))
        self.assertTrue(result.passed)
        self.assertEqual(len(result.rounds), 1)
        record = json.loads(Path(result.record_path).read_text(encoding="utf-8"))
        self.assertEqual(record["status"], "passed")
        self.assertEqual(record["avoid_rounds"], [])
        self.assertIsNone(record["navin_verdict"])
        self.assertIn("S1-06", record["rules_used"])
        self.assertIn("notes", record["rounds"][0])
        raw = Path(result.record_path).read_text(encoding="utf-8")
        self.assertNotIn(base64.b64encode(b"\x89PNG" + b"1" * 40).decode(), raw)
        self.assertTrue(any(p.get("sha256") for p in record["inputs"]["user"] if p["type"] == "image"))

    def test_reviewer_findings_are_remade(self):
        reviewer = BrainFakeClient("openai", fail_reviews=1)
        maker = BrainFakeClient("anthropic")
        runner = SectionRunner(gateway(maker, reviewer), maker="anthropic", reviewer="openai", rulebook=self.book,
                               records_dir=self.tmp.name)
        result = runner.run(self.step(page_with()))
        self.assertTrue(result.passed)
        self.assertEqual(len(result.rounds), 2)
        self.assertTrue(result.rounds[0]["review_problems"][0].startswith("[reviewer] missing: offline missing row"))
        self.assertEqual(result.rounds[1]["mode"], "patch")
        record = json.loads(Path(result.record_path).read_text(encoding="utf-8"))
        self.assertEqual(record["avoid_rounds"], [1])

    def test_code_problems_skip_the_reviewer_and_fail_after_max_rounds(self):
        reviewer = BrainFakeClient("openai")
        runner = SectionRunner(gateway(None, reviewer), maker="anthropic", reviewer="openai", rulebook=self.book)
        result = runner.run(self.step(page_with(), check=lambda value: ["always wrong"]))
        self.assertEqual(result.status, "failed")
        self.assertEqual(len(result.rounds), 3)
        self.assertEqual(reviewer.calls, [])
        self.assertEqual(result.rounds[-1]["code_problems"], ["[code] always wrong"])

    def test_a_converging_answer_gets_extra_patch_rounds_at_no_reviewer_cost(self):
        """Task 045d, job B: five scripts failed after 3 rounds with 1-4 small residues, each round smaller than the last.
        A code-only rejection with ever fewer problems (at most 4) now continues, up to extra_rounds more rounds."""
        reviewer = BrainFakeClient("openai")
        runner = SectionRunner(gateway(None, reviewer), maker="anthropic", reviewer="openai", rulebook=self.book,
                               records_dir=self.tmp.name)
        counts = iter([6, 3, 2, 1, 0])                      # 6 → 3 → 2 → 1 → 0: converging from round 3 on
        step = self.step(page_with(), check=lambda value: [f"residue {n}" for n in range(next(counts))])
        result = runner.run(step)
        self.assertEqual(result.status, "passed")
        self.assertEqual(len(result.rounds), 5)
        self.assertEqual([r.get("extra_round", False) for r in result.rounds], [False, False, False, True, True])
        self.assertEqual(len(reviewer.calls), 1)            # the reviewer saw only the clean round
        record = json.loads(Path(result.record_path).read_text(encoding="utf-8"))
        self.assertEqual(record["avoid_rounds"], [1, 2, 3, 4])

    def test_extra_rounds_stop_when_the_answer_no_longer_converges_or_runs_out(self):
        reviewer = BrainFakeClient("openai")
        runner = SectionRunner(gateway(None, reviewer), maker="anthropic", reviewer="openai", rulebook=self.book)
        stuck = iter([5, 2, 2, 1])                          # round 3 equals round 2: no trend, stop at max_rounds
        result = runner.run(self.step(page_with(), check=lambda value: ["x"] * next(stuck)))
        self.assertEqual((result.status, len(result.rounds)), ("failed", 3))
        wide = iter([9, 8, 7, 6])                           # falling, but far above CONVERGING_MAX: stop at max_rounds
        result = runner.run(self.step(page_with(), check=lambda value: ["x"] * next(wide)))
        self.assertEqual((result.status, len(result.rounds)), ("failed", 3))
        slow = iter([4, 3, 2, 1, 1, 1, 1])                  # converging, then flat: extra rounds end after 3 at most
        step = self.step(page_with(), check=lambda value: ["x"] * next(slow))
        result = runner.run(step)
        self.assertEqual((result.status, len(result.rounds)), ("failed", 5))     # round 4 extra (2 → 1), round 5 flat: stop
        step = self.step(page_with(), check=lambda value: ["x"] * next(iter([4, 3, 2])))
        step.extra_rounds = 0
        result = runner.run(step)
        self.assertEqual((result.status, len(result.rounds)), ("failed", 3))
        self.assertEqual(reviewer.calls, [])

    def test_maker_error_is_recorded(self):
        class Broken(BrainFakeClient):
            def _respond(self, model, messages, schema):
                raise ProviderError("auth", "bad key", provider="anthropic")
        runner = SectionRunner(gateway(Broken("anthropic")), maker="anthropic", reviewer="openai", rulebook=self.book)
        result = runner.run(self.step(page_with()))
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.rounds[0]["maker_error"]["kind"], "auth")

    def test_reviewer_must_differ(self):
        with self.assertRaises(ValueError):
            SectionRunner(gateway(), maker="anthropic", reviewer="anthropic", rulebook=self.book)

    def test_safe_content(self):
        self.assertEqual(safe_content("x"), "x")
        self.assertNotIn("data", safe_content([IMAGE])[0])


def item(iid, **extra):
    base = {"item_id": iid, "kind": "paragraph", "parent_item_id": "", "source": "text", "block_ids": [], "where_on_page": "",
            "content": "Cells form tissues.", "content_type": "fact", "teachable": True,
            "teacher_understanding": [
                {"depth": 1, "ask": "what", "question": "What is a tissue?", "answer": "A group of similar cells doing one job.", "basis": "book"},
                {"depth": 2, "ask": "why", "question": "Why group?", "answer": "Division of labour makes work efficient.", "basis": "outside"}],
            "prerequisites": [], "exam_importance": "high", "exam_note": "", "tests_item_ids": [],
            "unpack": {"terms": [{"term": "tissue", "plain_meaning": "एक जैसे cells का समूह", "everyday_image": "ईंटों की दीवार"}],
                       "why_chain": [{"step": "एक काम के लिए कई cells साथ चाहिए", "basis": "book"}], "example_or_place": "त्वचा",
                       "consequence": "", "visual_verb": "", "level_extra": ""}}
    base.update(extra)
    return base


def page_value(items, boilerplate=()):
    return {"notes": {}, "page_summary": "", "items": items, "boilerplate_block_ids": list(boilerplate),
            "text_image_disagreements": []}


class PageChecks(unittest.TestCase):
    def test_good_page_passes(self):
        page = page_with((("p0001-b0001", "Cells form tissues."), ("p0001-b0002", "88")))
        value = page_value([item("i1", block_ids=["p0001-b0001"])], boilerplate=["p0001-b0002"])
        self.assertEqual(check_page(value, page), [])

    def test_uncovered_and_unknown_blocks(self):
        page = page_with((("p0001-b0001", "Cells form tissues."), ("p0001-b0002", "Muscles move.")))
        problems = check_page(page_value([item("i1", block_ids=["p0001-b0001", "p0009-b0001"])]), page)
        self.assertTrue(any("not blocks of this page" in p for p in problems))
        self.assertTrue(any("1 native text blocks are in no item" in p and "p0001-b0002" in p for p in problems))

    def test_tables_diagrams_and_parents(self):
        page = page_with(())
        items = [item("t", kind="table", source="image", teachable=False),
                 item("r", kind="table_row", source="image", parent_item_id="x"),
                 item("l", kind="diagram_label", source="image", parent_item_id="t")]
        problems = check_page(page_value(items), page)
        self.assertTrue(any("parent_item_id 'x' does not exist" in p for p in problems))
        self.assertTrue(any("table_row needs its table" in p for p in problems))
        self.assertTrue(any("diagram_label needs its diagram" in p for p in problems))
        self.assertTrue(any("one table_row item per row" in p for p in problems))

    def test_teacher_questions_required(self):
        page = page_with((("p0001-b0001", "Cells form tissues."),))
        shallow = item("i1", block_ids=["p0001-b0001"], content_type="process", teacher_understanding=[
            {"depth": 1, "ask": "what", "question": "What?", "answer": "Cells form tissues.", "basis": "book"}])
        problems = check_page(page_value([shallow]), page)
        self.assertTrue(any("at least two teacher questions" in p for p in problems))
        self.assertTrue(any("'why' or 'how'" in p for p in problems))
        self.assertTrue(any("a process item must answer the required questions ['how', 'when']" in p for p in problems))
        self.assertTrue(any("only repeats" in p for p in problems))

    def test_image_only_page_must_be_read_from_the_image(self):
        page = page_with((("p0001-b0001", "Science and Technology"), ("p0001-b0002", "93")))
        value = page_value([], boilerplate=["p0001-b0001", "p0001-b0002"])
        self.assertTrue(any("must be read from the image" in p for p in check_page(value, page)))

    def test_review_problems(self):
        self.assertEqual(review_problems({"verdict": "pass", "missing": [], "checklist": [{"rule_id": "S1-03", "met": True, "note": ""}]}), [])
        self.assertTrue(review_problems({"verdict": "fail"}))
        found = review_problems({"verdict": "fail", "missing": [{"what": "row 3", "where_on_page": "top table", "severity": "blocking"},
                                                                {"what": "a nuance", "where_on_page": "x", "severity": "minor"}],
                                 "checklist": [{"rule_id": "S1-03", "met": False, "note": "row 3 missing"}]})
        self.assertEqual(found, ["missing: row 3 (top table)"])
        self.assertEqual(review_problems({"verdict": "pass", "wrong": [{"item_id": "i1", "problem": "p", "fix": "f", "severity": "minor"}]}), [])

    def test_page_patch(self):
        from bie.brain.understanding import apply_page_patch
        previous = page_value([item("i1"), item("i2"), item("i3")], boilerplate=["b9"])
        patched = apply_page_patch(previous, {"notes": {"about": "x"}, "replace_items": [item("i2", content="fixed"), item("i4")],
                                              "remove_item_ids": ["i3"], "boilerplate_block_ids": [], "text_image_disagreements": []})
        self.assertEqual([i["item_id"] for i in patched["items"]], ["i1", "i2", "i4"])
        self.assertEqual(patched["items"][1]["content"], "fixed")
        self.assertEqual(patched["boilerplate_block_ids"], ["b9"])
        self.assertEqual(patched["notes"], {"about": "x"})


class ConnectChecks(unittest.TestCase):
    items = {"p001-i1": {"teachable": True, "kind": "paragraph"}, "p001-i2": {"teachable": True, "kind": "question"}}

    def value(self, **extra):
        base = {"concepts": [{"concept_id": "c1", "name": "Tissue", "item_ids": ["p001-i1", "p001-i2"], "content_type": "fact",
                              "core_explanation": ""}],
                "relations": [], "prerequisites_to_teach": [], "cross_references": [],
                "question_links": [{"question_item_id": "p001-i2", "tests_concepts": ["c1"]}], "teaching_order": ["c1"],
                "exam_focus": []}
        base.update(extra)
        return base

    def test_good_map_passes(self):
        self.assertEqual(check_connect(self.value(), self.items), [])

    def test_problems_found(self):
        bad = self.value(concepts=[{"concept_id": "c1", "name": "T", "item_ids": ["p001-i9"], "content_type": "fact", "core_explanation": ""}],
                         relations=[{"from_concept": "c1", "relation": "causes", "to_concept": "c7", "note": ""}],
                         question_links=[], teaching_order=["c1", "c2"])
        problems = check_connect(bad, self.items)
        for fragment in ("item 'p001-i9' does not exist", "teachable items belong to no concept", "unknown concept 'c7'",
                         "question p001-i2 is not linked", "teaching_order must list every concept"):
            self.assertTrue(any(fragment in p for p in problems), fragment)


class Chapter(unittest.TestCase):
    def test_item_ids_become_chapter_wide(self):
        class R:
            output = {"items": [item("t", kind="table"), item("r", kind="table_row", parent_item_id="t", tests_item_ids=["t"])]}
        items = _chapter_items([(7, R())])
        self.assertEqual(sorted(items), ["p007-r", "p007-t"])
        self.assertEqual(items["p007-r"]["parent_item_id"], "p007-t")
        self.assertEqual(items["p007-r"]["tests_item_ids"], ["p007-t"])
        self.assertEqual(items["p007-r"]["page"], 7)

    def test_page_ranges(self):
        self.assertEqual(parse_page_range("1-3,5", 6), [1, 2, 3, 5])
        self.assertEqual(parse_page_range("", 2), [1, 2])
        with self.assertRaises(ValueError):
            parse_page_range("4-9", 6)

    def test_offline_end_to_end_on_a_real_pdf_with_an_image_only_page(self):
        from structural_pdf_fixtures import positioned_text_pdf
        lines = ["Tissue is a group of similar cells.", "Muscle tissue helps in movement.", "Nervous tissue carries messages."]
        pdf = positioned_text_pdf([[(72, 720 - i * 20, text) for i, text in enumerate(lines)], [],
                                   [(72, 720, "Plants have meristematic tissue.")]])
        book = rulebook.load()
        with tempfile.TemporaryDirectory() as folder:
            runner = SectionRunner(gateway(None, BrainFakeClient("openai", fail_reviews=1)), maker="anthropic", reviewer="openai",
                                   rulebook=book, records_dir=Path(folder, "records"))
            chapter = run_chapter(pdf, COURSE, runner, folder, workers=1)
            self.assertEqual(chapter["quality"]["pages"], 3)
            self.assertEqual(chapter["quality"]["pages_passed"], 3)
            self.assertEqual(chapter["map_status"], "passed")
            self.assertEqual(chapter["quality"]["items_from_image"], 3)       # the blank page was read "from the image"
            self.assertEqual([p["rounds"] for p in chapter["pages"]], [2, 1, 1])
            self.assertTrue(Path(folder, "MAP.md").read_text(encoding="utf-8").startswith("# Chapter map · Test chapter"))
            saved = json.loads(Path(folder, "chapter_map.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["map"]["teaching_order"], ["c1", "c2", "c3"])
            self.assertEqual(len(list(Path(folder, "records").glob("*.json"))), 4)


if __name__ == "__main__":
    unittest.main()


class Lesson(unittest.TestCase):
    chapter = {
        "course": {"title": "T", "subject": "Biology", "learners": "UPSC", "exam": "UPSC", "language": "Hinglish"},
        "items": {"p001-i1": item("p001-i1", page=1), "p001-i2": item("p001-i2", page=1, teachable=False, teacher_understanding=[])},
        "map": {"concepts": [{"concept_id": "c1", "name": "Tissue", "item_ids": ["p001-i1", "p001-i2"], "content_type": "fact",
                              "core_explanation": "x"}],
                "prerequisites_to_teach": [{"name": "Cell", "why_needed": "x", "needed_for": ["c1"], "basis": "outside"}],
                "teaching_order": ["c1"], "relations": [], "exam_focus": []},
    }
    video = {"video_id": "v1", "title": "Tissue", "goal": "", "concept_ids": ["c1"], "prerequisites_taught": ["Cell"],
             "opening_hook": "", "story_or_analogy": "", "estimated_minutes": 5, "why_this_unit": ""}

    def beat(self, bid, say="ये tissue है।", covers=(), answers=()):
        return {"beat_id": bid, "purpose": "explain", "say": say, "covers_item_ids": list(covers), "answers": list(answers),
                "on_screen": "", "basis": "book"}

    def test_plan_checks(self):
        from bie.brain.lesson import check_plan
        # Navin, 23 October 2026: the prerequisites in one "pehle yeh jaan lo" video first, then topic videos of 6-8
        # minutes per book page (S2-01, S2-03); this chapter has one teachable page.
        first = dict(self.video, video_id="v0", kind="prerequisites", concept_ids=[], prerequisites_taught=["Cell"], estimated_minutes=6)
        topic = dict(self.video, kind="topic", prerequisites_taught=[], estimated_minutes=7)
        self.assertEqual(check_plan({"videos": [first, topic]}, self.chapter), [])
        problems = check_plan({"videos": [dict(self.video, concept_ids=["c9"], prerequisites_taught=[], estimated_minutes=0)]},
                              self.chapter)
        for fragment in ("unknown concept 'c9'", "concept c1 (Tissue) is in no video", "prerequisite 'Cell' is taught in no video",
                         "estimated_minutes must be at least 1", "the plan needs exactly one prerequisite video"):
            self.assertTrue(any(fragment in p for p in problems), fragment)

    def test_script_checks(self):
        from bie.brain.lesson import check_script, question_ids
        self.assertEqual(question_ids(self.chapter["items"]["p001-i1"]), ["p001-i1#q1", "p001-i1#q2"])
        good = {"beats": [self.beat("b1"), self.beat("b2", covers=["p001-i1"], answers=["p001-i1#q1", "p001-i1#q2"]),
                          self.beat("b3")]}
        self.assertEqual(check_script(good, self.chapter, self.video, "Hinglish"), [])
        bad = {"beats": [self.beat("b1", say="This is English only.", covers=["p009-i1"], answers=["p001-i1#q2"]),
                         self.beat("b1", say="Still English.")]}
        problems = check_script(bad, self.chapter, self.video, "Hinglish")
        # Only the question answered from the book (q1) must be answered; q2 is answered from outside (S2-02).
        for fragment in ("beat_id 'b1' is used more than once", "'p009-i1' is not an item of this video",
                         "1 items are covered by no beat", "1 teacher questions answered from the book are answered by no beat",
                         "Devanagari",
                         "more than a couple of beats"):
            self.assertTrue(any(fragment in p for p in problems), fragment)

    def test_script_patch(self):
        from bie.brain.lesson import apply_script_patch
        previous = {"title": "t", "beats": [self.beat("b1"), self.beat("b2"), self.beat("b3")]}
        patched = apply_script_patch(previous, {"notes": {}, "replace_beats": [self.beat("b2", say="नया")],
                                                "insert_beats": [{"after_beat_id": "b1", "beat": self.beat("b1a")},
                                                                 {"after_beat_id": "", "beat": self.beat("b0")}],
                                                "remove_beat_ids": ["b3"]})
        self.assertEqual([b["beat_id"] for b in patched["beats"]], ["b0", "b1", "b1a", "b2"])
        self.assertEqual(patched["beats"][3]["say"], "नया")

    def test_offline_chain_from_pdf_to_scripts(self):
        from structural_pdf_fixtures import positioned_text_pdf
        from bie.brain.lesson import run_lesson
        pdf = positioned_text_pdf([[(72, 720, "Tissue is a group of similar cells."), (72, 700, "Muscles help in movement.")]])
        book = rulebook.load()
        with tempfile.TemporaryDirectory() as folder:
            runner = SectionRunner(gateway(), maker="anthropic", reviewer="openai", rulebook=book, records_dir=Path(folder, "records"))
            chapter = run_chapter(pdf, COURSE, runner, folder, workers=1)
            lesson = run_lesson(chapter, COURSE, runner, folder, workers=1)
            self.assertTrue(lesson["quality"]["plan_passed"])
            self.assertEqual(lesson["quality"]["videos_passed"], lesson["quality"]["videos"])
            self.assertTrue(Path(folder, "SCRIPT.md").exists())
            self.assertTrue(Path(folder, "records", "lesson--plan.json").exists())
            self.assertTrue(Path(folder, "records", "lesson--script-v1.json").exists())


class Director(unittest.TestCase):
    beats = [{"beat_id": "b1", "say": "ज़रा सोचिए, neuron कैसे signal भेजता है?"},
             {"beat_id": "b2", "say": "Dendrite signal लेता है, axon आगे भेजता है।"}]

    def scene(self, sid, beat_ids, word="neuron", beat="b1", **extra):
        base = {"scene_id": sid, "beat_ids": beat_ids,
                "frame": {"process": "", "how_it_works": "", "when_or_sequence": "", "conditions_or_atmosphere": "", "who_or_what_changes": ""},
                "style": "", "setting": "",
                "elements": [{"element_id": "e1", "kind": "cell_or_micro", "shows": "A neuron with dendrites and axon.",
                              "parts_to_label": ["dendrite"], "detail": "anatomy", "source_item_ids": []}],
                "camera": [], "actions": [{"cue": {"beat_id": beat, "word": word}, "element_id": "e1", "action": "appear", "detail": ""}],
                "visual_math": [], "interaction": {"type": "none", "question_id": "", "prompt": "", "target_element_id": ""}}
        base.update(extra)
        return base

    def test_word_matching(self):
        from bie.brain.director import word_in
        self.assertTrue(word_in("Neuron", self.beats[0]["say"]))
        self.assertTrue(word_in("सोचिए", self.beats[0]["say"]))
        self.assertFalse(word_in("synapse", self.beats[0]["say"]))
        self.assertFalse(word_in("neur", self.beats[0]["say"]))

    def test_good_video_passes(self):
        from bie.brain.director import check_video
        value = {"scenes": [self.scene("s1", ["b1"]), self.scene("s2", ["b2"], word="axon", beat="b2")]}
        self.assertEqual(check_video(value, self.beats, set(), set()), [])

    def test_problems_found(self):
        from bie.brain.director import check_video
        bad = {"scenes": [self.scene("s1", ["b2"], word="synapse", beat="b2",
                                     interaction={"type": "pause_question", "question_id": "x#q1", "prompt": "?", "target_element_id": ""},
                                     camera=[{"cue": {"beat_id": "b1", "word": "neuron"}, "move": "zoom_in", "target_element_id": "e9", "note": ""}])]}
        problems = check_video(bad, self.beats, set(), set())
        for fragment in ("cue word 'synapse' is not spoken", "camera cue beat 'b1' is not one of this scene's beats",
                         "targets unknown element 'e9'", "pause question 'x#q1'", "1 beats are in no scene: b1"):
            self.assertTrue(any(fragment in p for p in problems), fragment)

    def test_patch_keeps_beat_order(self):
        from bie.brain.director import apply_patch
        previous = {"scenes": [self.scene("s2", ["b2"])]}
        patched = apply_patch(previous, {"notes": {}, "replace_scenes": [self.scene("s1", ["b1"])], "remove_scene_ids": []}, ["b1", "b2"])
        self.assertEqual([s["scene_id"] for s in patched["scenes"]], ["s1", "s2"])

    def test_offline_chain_reaches_the_director(self):
        from structural_pdf_fixtures import positioned_text_pdf
        from bie.brain.director import run_director
        from bie.brain.lesson import run_lesson
        pdf = positioned_text_pdf([[(72, 720, "Neurons carry messages."), (72, 700, "Muscles help in movement.")]])
        with tempfile.TemporaryDirectory() as folder:
            runner = SectionRunner(gateway(), maker="anthropic", reviewer="openai", rulebook=rulebook.load(), records_dir=Path(folder, "r"))
            chapter = run_chapter(pdf, COURSE, runner, folder, workers=1)
            lesson = run_lesson(chapter, COURSE, runner, folder, workers=1)
            director = run_director(chapter, lesson, COURSE, runner, folder, workers=1)
            self.assertEqual(director["quality"]["videos_passed"], director["quality"]["videos"])
            self.assertGreater(director["quality"]["scenes"], 0)
            self.assertTrue(Path(folder, "DIRECTOR.md").exists())


class Assets(unittest.TestCase):
    def opener(self, routes):
        class Response:
            def __init__(self, body):
                self.body = body

            def read(self, limit=-1):
                return self.body

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        def open_(request, timeout):
            for prefix, body in routes.items():
                if request.full_url.startswith(prefix):
                    self.assertTrue(request.get_header("User-agent").startswith("BIE-asset-search"))
                    return Response(body)
            raise AssertionError("unexpected url " + request.full_url)
        return open_

    def commons_reply(self):
        def page(index, title, licence, mime="image/png"):
            return {"index": index, "title": title, "imageinfo": [{
                "url": f"https://upload.wikimedia.org/{index}.png", "thumburl": f"https://upload.wikimedia.org/t{index}.png",
                "descriptionurl": f"https://commons.wikimedia.org/wiki/{title}", "width": 1200, "height": 800, "mime": mime,
                "extmetadata": {"LicenseShortName": {"value": licence}, "Artist": {"value": "<a href='x'>Servier</a>"},
                                "LicenseUrl": {"value": "https://creativecommons.org/licenses/by/4.0"}}}]}
        pages = {"1": page(1, "File:Neuron.png", "CC BY 4.0"), "2": page(2, "File:Cell.png", "CC BY-SA 4.0"),
                 "3": page(3, "File:Old.png", "Public domain"), "4": page(4, "File:Nc.png", "CC BY-NC 2.0"),
                 "5": page(5, "File:Movie.ogv", "CC0", mime="video/ogg")}
        return json.dumps({"query": {"pages": pages}}).encode()

    def test_licences(self):
        from bie.brain.assets import licence_allowed, normalise_licence
        self.assertEqual(normalise_licence("CC BY-SA 4.0"), "share-alike")      # the licence policy's classes (Task 046a-L)
        self.assertEqual(normalise_licence("Public domain"), "public-domain")
        self.assertEqual(normalise_licence("CC BY-NC-SA 2.0"), "non-commercial")
        self.assertTrue(licence_allowed("CC BY 4.0"))
        self.assertFalse(licence_allowed("CC BY-SA 4.0"))
        self.assertFalse(licence_allowed("CC BY-NC 2.0"))
        with self.assertRaises(TypeError):                                        # no switch opens share-alike for lessons
            licence_allowed("CC BY-SA 4.0", allow_share_alike=True)

    def test_commons_search_keeps_allowed_images_only(self):
        from bie.brain.assets import search_commons
        found = search_commons("neuron", opener=self.opener({"https://commons.wikimedia.org/": self.commons_reply()}))
        self.assertEqual([c.title for c in found], ["File:Neuron.png", "File:Old.png"])
        self.assertEqual(found[0].author, "Servier")
        with self.assertRaises(TypeError):                                        # Task 046a-L: the share-alike switch is gone
            search_commons("neuron", allow_share_alike=True, opener=self.opener({"https://commons.wikimedia.org/": self.commons_reply()}))

    def test_library_stores_once_with_licence_and_credits(self):
        from bie.brain.assets import AssetLibrary, AssetError, search_commons
        routes = {"https://commons.wikimedia.org/": self.commons_reply(), "https://upload.wikimedia.org/": b"\x89PNG fake"}
        candidate = search_commons("neuron", opener=self.opener(routes))[0]
        with tempfile.TemporaryDirectory() as folder:
            library = AssetLibrary(folder)
            first = library.add_candidate(candidate, tags=["neuron", "biology"], opener=self.opener(routes))
            again = library.add_candidate(candidate, tags=["nerve"], opener=self.opener(routes))
            self.assertEqual(first.asset_id, again.asset_id)
            reloaded = AssetLibrary(folder)
            self.assertEqual(reloaded.assets[first.asset_id].tags, ["biology", "nerve", "neuron"])
            self.assertEqual(reloaded.find(["neuron"])[0].asset_id, first.asset_id)
            self.assertEqual(reloaded.credits([first.asset_id]), ["File:Neuron.png · Servier · CC BY 4.0 (https://creativecommons.org/licenses/by/4.0) "
                                                                  "· https://commons.wikimedia.org/wiki/File:Neuron.png"])
            self.assertEqual(reloaded.lesson_check([first.asset_id]), [])
            from dataclasses import replace
            with self.assertRaises(AssetError):
                library.add_candidate(replace(candidate, licence="CC BY-NC 2.0"), opener=self.opener(routes))


class Streaming(unittest.TestCase):
    def transport(self, events, record):
        import io
        from bie.model_gateway.live.transport import HttpTransport

        class Response(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        def open_(request, timeout):
            record.append({"url": request.full_url, "body": json.loads(request.data), "accept": request.get_header("Accept")})
            text = "".join(f"data: {e if isinstance(e, str) else json.dumps(e)}\n\n" for e in events)
            return Response((": keep-alive\n\n" + text).encode())
        return HttpTransport(opener=open_)

    def test_openai_stream(self):
        record = []
        final = {"status": "completed", "model": "gpt-x", "usage": {"input_tokens": 5, "output_tokens": 7},
                 "output": [{"type": "message", "content": [{"type": "output_text", "text": "{\"a\": 1}"}]}]}
        client = OpenAIClient("k", transport=self.transport([{"type": "response.created"}, {"type": "response.output_text.delta", "delta": "{"},
                                                             {"type": "response.completed", "response": final}], record), stream=True)
        out = client.responses_create(model="m", messages=MESSAGES)
        self.assertEqual(out["content"], "{\"a\": 1}")
        self.assertEqual(out["usage"]["output_tokens"], 7)
        self.assertTrue(record[0]["body"]["stream"])
        self.assertEqual(record[0]["accept"], "text/event-stream")

    def test_openai_stream_without_completion_is_an_error(self):
        client = OpenAIClient("k", transport=self.transport([{"type": "response.created"}], []), stream=True)
        with self.assertRaises(ProviderError):
            client.responses_create(model="m", messages=MESSAGES)

    def test_anthropic_stream(self):
        events = [{"type": "message_start", "message": {"model": "claude-x", "usage": {"input_tokens": 9}}},
                  {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "{\"a\""}},
                  {"type": "content_block_delta", "delta": {"type": "text_delta", "text": ": 2}"}},
                  {"type": "message_delta", "delta": {"stop_reason": "end_turn"}, "usage": {"output_tokens": 4}},
                  {"type": "message_stop"}]
        out = AnthropicClient("k", transport=self.transport(events, []), stream=True).messages_create(model="m", messages=MESSAGES)
        self.assertEqual(out["content"], "{\"a\": 2}")
        self.assertEqual((out["usage"]["input_tokens"], out["usage"]["output_tokens"]), (9, 4))

    def test_gemini_stream(self):
        record = []
        events = [{"candidates": [{"content": {"parts": [{"text": "thinking", "thought": True}, {"text": "{\"a\""}]}}]},
                  {"candidates": [{"content": {"parts": [{"text": ": 3}"}]}, "finishReason": "STOP"}],
                   "usageMetadata": {"promptTokenCount": 3, "candidatesTokenCount": 2}, "modelVersion": "gemini-x"}]
        out = GeminiClient("k", transport=self.transport(events, record), stream=True).generate(model="m", messages=MESSAGES)
        self.assertEqual(out["content"], "{\"a\": 3}")
        self.assertIn(":streamGenerateContent?alt=sse", record[0]["url"])
        self.assertEqual(out["usage"]["input_tokens"], 3)

    def test_compat_stream(self):
        record = []
        events = [{"model": "m1", "choices": [{"delta": {"content": "{\"a\""}}]},
                  {"model": "m1", "choices": [{"delta": {"content": ": 4}"}, "finish_reason": "stop"}]},
                  {"model": "m1", "choices": [], "usage": {"prompt_tokens": 8, "completion_tokens": 3}}, "[DONE]"]
        out = OpenAICompatChatClient("k", transport=self.transport(events, record), stream=True).chat(model="m", messages=MESSAGES)
        self.assertEqual(out["content"], "{\"a\": 4}")
        self.assertEqual(out["usage"]["output_tokens"], 3)
        self.assertEqual(record[0]["body"]["stream_options"], {"include_usage": True})

    def test_compat_stream_error_event(self):
        events = [{"error": {"message": "budget exceeded"}}]
        with self.assertRaises(ProviderError):
            OpenAICompatChatClient("k", transport=self.transport(events, []), stream=True).chat(model="m", messages=MESSAGES)


class Resume(unittest.TestCase):
    def test_passed_pages_are_reused_not_paid_again(self):
        from structural_pdf_fixtures import positioned_text_pdf
        pdf = positioned_text_pdf([[(72, 720, "Tissue is a group of cells.")], [(72, 720, "Muscles move bones.")]])
        with tempfile.TemporaryDirectory() as folder:
            maker = BrainFakeClient("anthropic")
            runner = SectionRunner(gateway(maker), maker="anthropic", reviewer="openai", rulebook=rulebook.load())
            first = run_chapter(pdf, COURSE, runner, Path(folder, "one"), workers=1)
            first["pages"][1]["status"] = "failed"           # pretend page 2 failed last time
            calls = len(maker.calls)
            second = run_chapter(pdf, COURSE, runner, Path(folder, "two"), workers=1, previous_chapter=first)
            self.assertEqual([p["reused"] for p in second["pages"]], [True, False])
            self.assertEqual(sorted(second["items"]), sorted(first["items"]))
            self.assertEqual(second["items"]["p001-i1"]["content"], "Tissue is a group of cells.")
            self.assertEqual(len(maker.calls) - calls, 2)              # page 2 again plus the chapter map


class Notes(unittest.TestCase):
    chapter = {"items": {"p001-i1": item("p001-i1", page=1), "p001-q": item("p001-q", page=1, kind="question", teachable=False,
                                                                           teacher_understanding=[])}}

    def slide(self, sid, **extra):
        base = {"slide_id": sid, "ask": "what", "question": "Tissue क्या है?", "essence": "Cells ka group.", "answer": "a", "deep_dive": "b",
                "visual": {"type": "difference_table", "title": "", "steps": [], "events": [], "columns": ["A", "B"],
                           "rows": [{"label": "x", "cells": ["1", "2"]}], "series": [], "nodes": [], "edges": []},
                "source_item_ids": ["p001-i1"], "basis": "book", "not_in_book": "", "pyq_item_ids": ["p001-q"]}
        base.update(extra)
        return base

    def test_checks(self):
        from bie.brain.notes import check_slides
        self.assertEqual(check_slides({"slides": [self.slide("n1")]}, self.chapter, {"p001-i1"}), [])
        bad_visual = dict(self.slide("n1")["visual"], rows=[{"label": "x", "cells": ["1"]}])
        problems = check_slides({"slides": [self.slide("n1", source_item_ids=[], pyq_item_ids=["p001-i1"], visual=bad_visual),
                                            self.slide("n1", essence="")]}, self.chapter, {"p001-i1", "p001-i9"})
        for fragment in ("slide_id 'n1' is used more than once", "needs its source items", "is not a question item",
                         "has 1 cells for 2 columns", "essence is empty", "1 teachable items are the source of no slide"):
            self.assertTrue(any(fragment in p for p in problems), fragment)

    def test_html_is_self_contained_and_safe(self):
        from bie.brain.notes_render import render_notes_html
        notes = {"course": {"title": "T <b>", "subject": "Bio", "learners": "UPSC", "language": "Hinglish"}, "rulebook_version": "r",
                 "concepts": [{"name": "Tissue", "slides": [self.slide("n1", answer="</script><script>alert(1)</script>")]}],
                 "items": {"p001-i1": {"page": 1}}}
        page = render_notes_html(notes)
        self.assertNotIn("</script><script>alert(1)", page)
        self.assertIn("T &lt;b&gt;", page)
        self.assertNotIn("http://", page.replace("http://www.w3.org", ""))
        self.assertNotIn("<link", page)

    def test_offline_notes(self):
        from structural_pdf_fixtures import positioned_text_pdf
        from bie.brain.notes import run_notes
        pdf = positioned_text_pdf([[(72, 720, "Tissue is a group of cells."), (72, 700, "Muscles move bones.")]])
        with tempfile.TemporaryDirectory() as folder:
            runner = SectionRunner(gateway(), maker="anthropic", reviewer="openai", rulebook=rulebook.load())
            chapter = run_chapter(pdf, COURSE, runner, folder, workers=1)
            notes = run_notes(chapter, COURSE, runner, folder, workers=1)
            self.assertEqual(notes["quality"]["concepts_passed"], notes["quality"]["concepts"])
            self.assertGreater(notes["quality"]["slides"], 0)
            self.assertIn("application/json", Path(folder, "NOTES.html").read_text(encoding="utf-8"))


class Game(unittest.TestCase):
    chapter = {"items": {"p001-i1": item("p001-i1", page=1), "p001-i2": item("p001-i2", page=1)}}

    def mission(self, mid, **extra):
        base = {"mission_id": mid, "title": "Signal Runner", "item_ids": ["p001-i1", "p001-i2"], "content_type": "process",
                "mechanic": "run_process", "player_role": "an impulse", "goal": "Reach the synapse.", "scene": "A neuron.",
                "interactions": ["drag"], "steps": [{"step_id": "s1", "player_does": "Release the neurotransmitter at the right time.",
                                                     "correct_when": "at the axon end", "wrong_moves": [
                    {"move": "too early", "what_breaks": "the signal fades", "why": "nothing to cross the gap", "item_ids": ["p001-i1"]}]}],
                "win": "", "feedback_on_win": "", "replay_twist": "", "assets_needed": []}
        base.update(extra)
        return base

    def test_checks(self):
        from bie.brain.game import check_design
        self.assertEqual(check_design({"missions": [self.mission("m1")]}, self.chapter), [])
        quiz = self.mission("m1", item_ids=["p001-i1", "p009-x"], goal="Which of the following is a tissue?",
                            steps=[{"step_id": "s1", "player_does": "tap", "correct_when": "", "wrong_moves": []}])
        problems = check_design({"missions": [quiz, self.mission("m1", interactions=[])]}, self.chapter)
        for fragment in ("mission_id 'm1' is used more than once", "unknown item 'p009-x'", "reads like a multiple-choice question",
                         "no wrong move shows what breaks", "has no interaction"):
            self.assertTrue(any(fragment in p for p in problems), fragment)
        self.assertTrue(any("1 teachable items are played in no mission" in p
                            for p in check_design({"missions": [self.mission("m1", item_ids=["p001-i1"])]}, self.chapter)))

    def test_offline_game_design(self):
        from structural_pdf_fixtures import positioned_text_pdf
        from bie.brain.game import run_game_design
        pdf = positioned_text_pdf([[(72, 720, "Neurons carry messages."), (72, 700, "Muscles move bones.")]])
        with tempfile.TemporaryDirectory() as folder:
            runner = SectionRunner(gateway(), maker="anthropic", reviewer="openai", rulebook=rulebook.load())
            chapter = run_chapter(pdf, COURSE, runner, folder, workers=1)
            design = run_game_design(chapter, COURSE, runner, folder)
            self.assertTrue(design["quality"]["passed"])
            self.assertTrue(Path(folder, "GAME.md").exists())


def png_bytes(width=64, height=48, color=(200, 120, 90)):
    import io
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (width, height), color).save(buf, format="PNG")
    return buf.getvalue()


class Visual(unittest.TestCase):
    scene = {"scene_id": "s1", "beat_ids": ["b1", "b2"], "elements": [
        {"element_id": "e1", "kind": "cell_or_micro", "shows": "A neuron", "parts_to_label": ["axon"], "detail": "anatomy",
         "source_item_ids": []}], "camera": [], "actions": [], "visual_math": [],
        "interaction": {"type": "none", "question_id": "", "prompt": "", "target_element_id": ""},
        "frame": {"process": "", "how_it_works": "", "when_or_sequence": "", "conditions_or_atmosphere": "", "who_or_what_changes": ""},
        "style": "", "setting": ""}
    says = {"b1": "ज़रा सोचिए, neuron कैसे signal भेजता है?", "b2": "Axon signal आगे भेजता है।"}

    def layer(self, lid, kind, **extra):
        empty = {"x": 0, "y": 0, "w": 0, "h": 0}
        base = {"id": lid, "type": kind, "cue": {"beat_id": "b1", "word": "neuron"}, "until": {"beat_id": "", "word": ""},
                "box": {"x": 0.1, "y": 0.1, "w": 0.4, "h": 0.4}, "element_id": "", "text": "", "subtitle": "", "tone": "accent",
                "anchor": {"layer": "", "x": 0, "y": 0}, "target_layer": "", "region": empty, "path": [], "entries": [], "columns": [],
                "rows": [], "focus": [], "from_ref": {"layer": "", "x": 0, "y": 0}, "to_ref": {"layer": "", "x": 0, "y": 0}}
        base.update(extra)
        return base

    def test_checks(self):
        from bie.brain.visual import check_layout
        assets = {"e1": {"src": "assets/x.png", "credit": "c"}}
        good = {"layers": [self.layer("img", "image", element_id="e1"),
                           self.layer("lab", "label", box={"x": 0.6, "y": 0.1, "w": 0.3, "h": 0.1}, text="Axon",
                                      anchor={"layer": "img", "x": 0.8, "y": 0.5}, cue={"beat_id": "b2", "word": "axon"})],
                "camera": [{"cue": {"beat_id": "b2", "word": "signal"}, "layer": "img", "region": {"x": 0.5, "y": 0.3, "w": 0.4, "h": 0.4}, "frames": 30}]}
        self.assertEqual(check_layout(good, self.scene, self.says, assets), [])
        bad = {"layers": [self.layer("img", "image", element_id="e9", cue={"beat_id": "b1", "word": "synapse"}),
                          self.layer("t1", "title", text="x", box={"x": 0.2, "y": 0.2, "w": 0.4, "h": 0.4}),
                          self.layer("lab", "label", text="", anchor={"layer": "zz", "x": 0, "y": 0}, box={"x": 0.9, "y": 0.1, "w": 0.3, "h": 0.1}),
                          self.layer("f", "flow", target_layer="img", path=[{"x": 0, "y": 0}])],
               "camera": [{"cue": {"beat_id": "b3", "word": "x"}, "layer": "nope", "region": {"x": 0, "y": 0, "w": 1, "h": 1}, "frames": 30}]}
        problems = check_layout(bad, self.scene, self.says, assets)
        for fragment in ("cue word 'synapse' is not spoken", "has no chosen picture", "overlap on screen", "needs short text",
                         "anchor layer 'zz' does not exist", "box must lie inside the screen", "at least two path points",
                         "cue beat 'b3' is not a beat", "layer 'nope' does not exist"):
            self.assertTrue(any(fragment in p for p in problems), fragment)

    def test_scene_spec_uses_spoken_word_frames(self):
        from bie.brain.video import timing
        from bie.brain.visual import key_frames, to_scene_spec
        beats = [{"beat_id": b, "say": s} for b, s in self.says.items()]
        timeline = timing.build(beats, [self.scene])
        layout = {"layers": [self.layer("img", "image", element_id="e1"),
                             self.layer("lab", "label", text="Axon", cue={"beat_id": "b2", "word": "axon"},
                                        anchor={"layer": "img", "x": 0.8, "y": 0.5})],
                  "camera": [{"cue": {"beat_id": "b2", "word": "signal"}, "layer": "img", "region": {"x": 0.5, "y": 0.3, "w": 0.4, "h": 0.4}, "frames": 30}]}
        spec = to_scene_spec(layout, self.scene, timeline, self.says, {"e1": {"src": "assets/x.png", "credit": "A · CC BY"}}, [])
        b2_start = timeline["s1"]["beats"]["b2"][0]
        self.assertEqual(spec["layers"][1]["at"], b2_start)              # "Axon" is the first word of b2
        self.assertEqual(spec["layers"][1]["anchor"], {"layer": "img", "point": {"x": 0.8, "y": 0.5}})
        self.assertGreater(spec["camera"][1]["at"], b2_start)
        self.assertEqual(spec["camera"][1]["layer"], "img")
        self.assertTrue(all(0 <= f < spec["duration"] for f in key_frames(spec)))

    def test_layout_patch(self):
        from bie.brain.visual import apply_patch
        previous = {"layers": [self.layer("a", "title"), self.layer("b", "title")], "camera": [1]}
        patched = apply_patch(previous, {"notes": {}, "replace_layers": [self.layer("b", "title", text="new")], "remove_layer_ids": ["a"], "camera": []})
        self.assertEqual([l["id"] for l in patched["layers"]], ["b"])
        self.assertEqual(patched["camera"], [])

    def test_offline_visuals_from_director(self):
        from structural_pdf_fixtures import positioned_text_pdf
        from bie.brain.director import run_director
        from bie.brain.lesson import run_lesson
        from bie.brain.visual import run_visual
        commons = json.dumps({"query": {"pages": {"1": {"index": 1, "title": "File:Neuron.png", "imageinfo": [{
            "url": "https://upload.wikimedia.org/a/Neuron.png", "thumburl": "https://upload.wikimedia.org/thumb/a/Neuron.png/800px-Neuron.png",
            "descriptionurl": "https://commons.wikimedia.org/wiki/File:Neuron.png", "width": 800, "height": 600, "mime": "image/png",
            "extmetadata": {"LicenseShortName": {"value": "CC BY 4.0"}, "Artist": {"value": "Someone"},
                            "LicenseUrl": {"value": "https://creativecommons.org/licenses/by/4.0"}}}]}}}}).encode()   # a CC BY credit needs all four fields
        picture = png_bytes()

        class Response:
            def __init__(self, body):
                self.body = body

            def read(self, limit=-1):
                return self.body

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        def opener(request, timeout):
            return Response(commons if "commons.wikimedia.org/w/api.php" in request.full_url else picture)

        pdf = positioned_text_pdf([[(72, 720, "Neurons carry messages."), (72, 700, "Muscles move bones.")]])
        with tempfile.TemporaryDirectory() as folder:
            runner = SectionRunner(gateway(), maker="anthropic", reviewer="openai", rulebook=rulebook.load(), records_dir=Path(folder, "r"))
            chapter = run_chapter(pdf, COURSE, runner, folder, workers=1)
            lesson = run_lesson(chapter, COURSE, runner, folder, workers=1)
            director = run_director(chapter, lesson, COURSE, runner, folder, workers=1)
            for video in director["videos"]:                       # make the fake director ask for one picture
                video["scenes"][0]["elements"][0]["kind"] = "cell_or_micro"
            visual = run_visual(chapter, lesson, director, COURSE, runner, folder, workers=1, opener=opener)
            self.assertEqual(visual["quality"]["scenes_passed"], visual["quality"]["scenes"])
            self.assertGreaterEqual(visual["quality"]["pictures_chosen"], 1)
            spec = json.loads(next(Path(folder, "video_specs").glob("*.json")).read_text(encoding="utf-8"))
            self.assertTrue(spec["scenes"])
            self.assertTrue(any(l["type"] == "image" and l["src"].startswith("assets/files/") for s in spec["scenes"] for l in s["layers"]))
            self.assertIn("CC BY 4.0", "\n".join(visual["credits"]))
            self.assertEqual(visual["credits"], ["File:Neuron.png · Someone · CC BY 4.0 (https://creativecommons.org/licenses/by/4.0) · "
                                                 "https://commons.wikimedia.org/wiki/File:Neuron.png"])
            self.assertTrue(all(v["status"] == "spec_written" and v["credits"] for v in visual["videos"]))
            self.assertEqual(visual["quality"]["videos_stopped_by_licence"], 0)

    def test_the_licence_gate_stops_a_video_that_would_show_a_z_anatomy_model(self):
        # Task 046a-L: an asset a lesson may not use stops that video before its layout is paid for; nothing is swapped
        from unittest import mock
        from structural_pdf_fixtures import positioned_text_pdf
        from bie.brain.assets import Candidate
        from bie.brain.director import run_director
        from bie.brain.lesson import run_lesson
        from bie.brain.visual import run_visual
        picture = png_bytes()
        heart = Candidate("z_anatomy", "CardioVascular41: heart", "https://github.com/LluisV/Z-Anatomy", "https://example.org/heart.png",
                          "https://example.org/heart.png", 64, 48, "image/png", "CC BY-SA 4.0", "https://creativecommons.org/licenses/by-sa/4.0/",
                          "Z-Anatomy project", "Z-Anatomy, CC BY-SA 4.0")

        class Response:
            def __init__(self, body):
                self.body = body

            def read(self, limit=-1):
                return self.body

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        pdf = positioned_text_pdf([[(72, 720, "Neurons carry messages."), (72, 700, "Muscles move bones.")]])
        with tempfile.TemporaryDirectory() as folder, mock.patch("bie.brain.visual._fetch_candidates", return_value=[heart]):
            runner = SectionRunner(gateway(), maker="anthropic", reviewer="openai", rulebook=rulebook.load(), records_dir=Path(folder, "r"))
            chapter = run_chapter(pdf, COURSE, runner, folder, workers=1)
            lesson = run_lesson(chapter, COURSE, runner, folder, workers=1)
            director = run_director(chapter, lesson, COURSE, runner, folder, workers=1)
            for video in director["videos"]:
                video["scenes"][0]["elements"][0]["kind"] = "cell_or_micro"
            visual = run_visual(chapter, lesson, director, COURSE, runner, folder, workers=1, opener=lambda request, timeout: Response(picture))
            stopped = [v for v in visual["videos"] if v["status"] == "stopped_by_licence"]
            self.assertTrue(stopped)
            self.assertEqual(visual["quality"]["videos_stopped_by_licence"], len(stopped))
            self.assertTrue(all("share-alike" in p for v in stopped for p in v["licence_problems"]))
            self.assertTrue(all(v["scenes"] == [] for v in stopped))                       # no layout was run for them
            self.assertEqual(sorted(p.stem for p in Path(folder, "video_specs").glob("*.json")),
                             sorted(v["video_id"] for v in visual["videos"] if v["status"] == "spec_written"))
            self.assertEqual(visual["credits"], [])
            self.assertIn("Stopped by the lesson licence gate", Path(folder, "VISUAL.md").read_text(encoding="utf-8"))
