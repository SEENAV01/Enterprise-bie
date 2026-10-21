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


SIMPLE_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["thinking", "items"],
                 "properties": {"thinking": {"type": "object"}, "items": {"type": "array", "items": {"type": "object"}}}}
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
        self.assertIn("thinking", record["rounds"][0])
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
            "prerequisites": [], "exam_importance": "high", "exam_note": "", "tests_item_ids": []}
    base.update(extra)
    return base


def page_value(items, boilerplate=()):
    return {"thinking": {}, "page_summary": "", "items": items, "boilerplate_block_ids": list(boilerplate),
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
        self.assertTrue(any("a process needs a 'how'" in p for p in problems))
        self.assertTrue(any("only repeats" in p for p in problems))

    def test_image_only_page_must_be_read_from_the_image(self):
        page = page_with((("p0001-b0001", "Science and Technology"), ("p0001-b0002", "93")))
        value = page_value([], boilerplate=["p0001-b0001", "p0001-b0002"])
        self.assertTrue(any("must be read from the image" in p for p in check_page(value, page)))

    def test_review_problems(self):
        self.assertEqual(review_problems({"verdict": "pass", "missing": [], "checklist": [{"rule_id": "S1-03", "met": True, "note": ""}]}), [])
        self.assertTrue(review_problems({"verdict": "fail"}))
        found = review_problems({"verdict": "fail", "missing": [{"what": "row 3", "where_on_page": "top table"}],
                                 "checklist": [{"rule_id": "S1-03", "met": False, "note": "row 3 missing"}]})
        self.assertEqual(found, ["missing: row 3 (top table)", "rule S1-03 not met: row 3 missing"])


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
