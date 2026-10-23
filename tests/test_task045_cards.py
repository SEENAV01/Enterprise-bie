"""Task 045: content-type detection, the naksha, task cards, the old engines as checks and Section 2 on the card (offline)."""
from __future__ import annotations

import ast
import contextlib
import copy
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests" / "productization" / "document_intelligence"))

import run_brain  # noqa: E402
from bie.brain import cards, engines, rulebook  # noqa: E402
from bie.brain import content_types as ct  # noqa: E402
from bie.brain import naksha as nk  # noqa: E402
from bie.brain.fake import BrainFakeClient  # noqa: E402
from bie.brain.lesson import (FRAME, apply_script_patch, check_script, plan_card, script_card, script_prefixes,  # noqa: E402
                              spoken_problems, _prefix, PLAN_SCHEMA, PLAN_SCHEMA_ID, PLAN_ROLE, PLAN_HOW)
from bie.brain.pages import Block, Page  # noqa: E402
from bie.brain.runner import SectionRunner  # noqa: E402
from bie.brain.understanding import (Course, check_page, connect_step, likely_boilerplate, page_prefixes, page_step,  # noqa: E402
                                     run_chapter)
from bie.model_gateway.claude_adapter import ClaudeAdapter  # noqa: E402
from bie.model_gateway.gpt_adapter import GPTAdapter  # noqa: E402
from bie.model_gateway.live.gateway import LiveGateway  # noqa: E402
from bie.model_gateway.live.messages import text_of  # noqa: E402
from structural_pdf_fixtures import positioned_text_pdf  # noqa: E402

COURSE = Course("10. Tissues and Its Types", "Science and Technology", "UPSC aspirants", "UPSC", "Hinglish")
TYPES = ct.load()
BOOK = rulebook.load()
ENV = {"BIE_MODEL_PRICES_JSON": json.dumps({"fake": [100.0, 100.0]}), "BIE_USD_INR": "100"}


def blocks(*texts, page=3):
    return tuple(Block(f"p{page:04d}-b{n:04d}", text, (0, 0, 1, 1)) for n, text in enumerate(texts, 1))


def page_of(*texts, number=3, image=True):
    return Page(number, blocks(*texts, page=number), b"\x89PNG" + b"7" * 40 if image else None)


TISSUE_PAGE = ("Science and Technology", "There are mainly four different types of tissues present in our body.",
               "1. Epithelial- provides covering or lining", "2. Muscular- helps in movement",
               " Collagen fibres are made up of fibrous protein, collagen.", "89")


def qa(*asks):
    return [{"depth": 1 if n == 0 else 2, "ask": a, "question": f"Question {a}?", "answer": f"Answer about {a} here.",
             "basis": "book"} for n, a in enumerate(asks)]


def item(iid, block_ids, kind_type, *asks, kind="paragraph", note="", teachable=True, content=None, source="text"):
    return {"item_id": iid, "kind": kind, "parent_item_id": "", "source": source, "block_ids": list(block_ids),
            "where_on_page": "", "content": content or f"content of {iid}", "content_type": kind_type, "type_note": note,
            "teachable": teachable, "teacher_understanding": qa(*asks) if teachable else [], "prerequisites": [],
            "exam_importance": "high", "exam_note": "", "tests_item_ids": []}


def gateway(maker=None, reviewer=None):
    routes = {"anthropic": ClaudeAdapter(maker or BrainFakeClient("anthropic"), "fake-claude"),
              "openai": GPTAdapter(reviewer or BrainFakeClient("openai"), "fake-gpt")}
    return LiveGateway(routes, sleep=lambda s: None)


def run(argv, *, client=None):
    out = io.StringIO()
    patches = [mock.patch.dict(os.environ, ENV), contextlib.redirect_stdout(out)]
    if client is not None:
        patches.append(mock.patch.object(run_brain, "BrainFakeClient", client))
    with contextlib.ExitStack() as stack:
        for patch in patches:
            stack.enter_context(patch)
        code = run_brain.main(argv)
    return code, out.getvalue()


# ---------------------------------------------------------------- content types in code

class ContentTypeDetection(unittest.TestCase):
    def test_the_type_map_loads_with_required_questions_and_words(self):
        self.assertEqual(TYPES.ids, ("process", "structure", "classification", "comparison", "timeline", "cause_effect",
                                     "facts_numbers", "figure", "definition"))
        self.assertEqual(TYPES.required_asks("process"), ("how", "when"))
        self.assertEqual(TYPES.required_words("process"), ("kaise", "kab"))
        self.assertEqual(TYPES.required_words("comparison"), ("tulna",))
        self.assertEqual(len(TYPES.pattern("timeline")), 6)
        self.assertEqual(TYPES.from_legacy("fact"), "facts_numbers")
        self.assertEqual(TYPES.from_legacy("formula"), "facts_numbers")
        self.assertEqual(TYPES.from_legacy("example"), ct.NONE)
        self.assertEqual(TYPES.from_legacy("question"), ct.NONE)
        self.assertEqual(TYPES.from_legacy("process"), "process")
        raw = json.loads(ct.PATH.read_text(encoding="utf-8"))
        process = next(t for t in raw["types"] if t["id"] == "process")
        self.assertIn(ct.NUMBERED_LIST_HINT, process["detection_hints"]["patterns"])

    def test_single_lines(self):
        cases = {
            "There are mainly four different types of tissues present in our body.": ("classification", "strong"),
            "TISSUE: Cells combine to perform same function.": ("definition", "strong"),
            "In leaf cells this tissue is called CHLORENCHYMA.": ("definition", "strong"),
            "The Revolt began in 1857 and spread to Delhi.": ("timeline", "strong"),
            "The difference between xylem and phloem is clear.": ("comparison", "strong"),
            "Xylem consists of tracheids, vessels and fibres.": ("structure", "strong"),
            "Prices rise because demand grows, therefore wages rise.": ("cause_effect", "strong"),
            "Fig. 6.9: Different epithelial tissues": ("figure", "strong"),
            "The lining is a single layer.": ("structure", "weak"),
        }
        for text, (kind, strength) in cases.items():
            with self.subTest(text=text):
                got = ct.propose(text)
                self.assertEqual((got.type, got.strength), (kind, strength), got.evidence)
        self.assertIsNone(ct.propose("Unbranched").type)
        self.assertNotEqual(ct.propose("Example: Stomach, Intestine, eye, blood vessel etc.").type, "definition")
        self.assertNotEqual(ct.propose("Occurrence: In leaf stalks and stems of dicots.").type, "definition")
        tie = ct.propose("Phloem is made up of five types of cells: sieve cells and companion cells.")
        self.assertEqual(tie.strength, "weak")           # two types equally likely: a hint, never a correction
        self.assertIn("pattern 'types of'", " ".join(ct.propose("Four types of tissue.").evidence))

    def test_a_list_takes_the_type_of_the_line_that_introduces_it(self):
        page = blocks("There are mainly four different types of tissues present in our body.",
                      "1. Epithelial- provides covering or lining", "2. Muscular- helps in movement",
                      " Epithelium covers most organs.", "Types:", "a. Skeletal", "b. Smooth", "Steps:",
                      "1. Mix the solution")
        got = ct.propose_blocks(page)
        kinds = [got[b.id].type for b in page]
        self.assertEqual(kinds[:3], ["classification"] * 3)
        self.assertIsNone(kinds[3])                       # the marker changed: the list ended
        self.assertEqual(kinds[4:7], ["classification"] * 3)
        self.assertIsNone(kinds[8])                       # "Steps:" is no strong lead-in; a numbered line alone is no process
        self.assertIn("list under", got[page[1].id].evidence[0])

    def test_comparison_of_maker_types_with_the_code(self):
        page = blocks(*TISSUE_PAGE[1:5])
        proposals = ct.propose_blocks(page)
        items = [item("i1", [page[0].id], "classification", "which", "difference", "why"),
                 item("i2", [page[1].id], "facts_numbers", "what", "evidence", "why"),
                 item("i3", [page[2].id], "facts_numbers", "what", "evidence", "why", note="each line names one kind's job"),
                 item("i4", [page[3].id], "structure", "what", "where", "why"),
                 item("i5", [], "figure", "what", "which", "why", source="image"),
                 item("i6", [], "facts_numbers", "what", "why", kind="question"),
                 item("i7", [page[3].id], "comparison", "compare", "difference", "why", kind="table_row")]
        rows = {r["item_id"]: r for r in ct.compare(items, proposals)}
        self.assertEqual({k: r["status"] for k, r in rows.items()},
                         {"i1": "agree", "i2": "disagree", "i3": "explained", "i4": "agree", "i5": "code_silent", "i6": "role",
                          "i7": "follows_parent"})
        self.assertEqual(rows["i2"]["code_type"], "classification")
        self.assertEqual(ct.summary(rows.values())["disagree"], 1)


# ---------------------------------------------------------------- naksha

def small_chapter(types="new"):
    fact = "facts_numbers" if types == "new" else "fact"
    items = {
        "p001-i1": dict(item("p001-i1", ["p0001-b0001"], "definition", "what", "evidence", "why",
                             content="A tissue is a group of similar cells doing one job."), page=1),
        "p001-i2": dict(item("p001-i2", ["p0001-b0002"], fact, "what", "evidence", "why",
                             content="The heart beats 72 times per minute at rest " + "and keeps beating " * 10), page=1),
        "p001-i3": dict(item("p001-i3", [], "classification", "which", "difference", "why", kind="table", source="image"), page=1),
        "p001-i4": dict(item("p001-i4", [], "comparison", "compare", "difference", "why", kind="table_row", source="image"),
                        page=1, parent_item_id="p001-i3"),
        "p002-i1": dict(item("p002-i1", ["p0002-b0001"], "process", "how", "when", "why",
                             content="Cells divide by mitosis in steps."), page=2),
        "p002-i2": dict(item("p002-i2", ["p0002-b0002"], "none", kind="heading", teachable=False), page=2),
        "p002-i3": dict(item("p002-i3", ["p0002-b0003"], "none", "what", "why", kind="question"), page=2,
                        tests_item_ids=["p002-i1"]),
    }
    if types != "new":
        items["p001-i1"]["content_type"] = "example"
    concepts = [{"concept_id": "c1", "name": "Tissue", "item_ids": ["p001-i1", "p001-i2"], "content_type": "definition",
                 "core_explanation": "x"},
                {"concept_id": "c2", "name": "Kinds of tissue", "item_ids": ["p001-i3", "p001-i4"], "content_type": "classification",
                 "core_explanation": "x"},
                {"concept_id": "c3", "name": "Cell division", "item_ids": ["p002-i1", "p002-i2", "p002-i3"], "content_type": "process",
                 "core_explanation": "x"}]
    return {"schema": "bie.brain.chapter-map/2", "course": {"title": "T", "subject": "Biology", "learners": "UPSC", "exam": "UPSC",
                                                           "language": "Hinglish"},
            "source_sha256": "a" * 64, "page_count": 2, "rulebook_version": BOOK.version, "pages": [{"page": 1}, {"page": 2}],
            "items": items,
            "map": {"chapter_summary": "Tissues.", "concepts": concepts,
                    "relations": [{"from_concept": "c2", "relation": "depends_on", "to_concept": "c1", "note": ""},
                                  {"from_concept": "c3", "relation": "causes", "to_concept": "c2", "note": ""},
                                  {"from_concept": "c2", "relation": "contrasts_with", "to_concept": "c3", "note": ""}],
                    "prerequisites_to_teach": [{"name": "Cell", "why_needed": "x", "needed_for": ["c1"], "basis": "outside"}],
                    "cross_references": [], "question_links": [{"question_item_id": "p002-i3", "tests_concepts": ["c3"]}],
                    "teaching_order": ["c1", "c2", "c3"], "exam_focus": [{"concept_id": "c2", "why": "asked often"}]}}


class Naksha(unittest.TestCase):
    def test_compact_rows_ids_types_questions_links(self):
        built = nk.build(small_chapter())
        rows = {r[0]: r for r in built["items"]}
        self.assertEqual(sorted(rows), ["p001-i1", "p001-i2", "p001-i3", "p001-i4", "p002-i1", "p002-i3"])   # no heading
        self.assertEqual(rows["p002-i1"], ["p002-i1", "process", 2, "Cells divide by mitosis in steps.", "kaise,kab", "h"])
        self.assertLessEqual(len(rows["p001-i2"][3]), nk.SHORT)
        self.assertTrue(rows["p001-i2"][3].endswith("…"))
        links = {tuple(link) for link in built["links"]}
        for expected in [("p001-i4", "part", "p001-i3"), ("p002-i3", "test", "p002-i1"), ("c2", "pre", "c1"),
                         ("c3", "cause", "c2"), ("c2", "compare", "c3"), ("p002-i3", "test", "c3")]:
            self.assertIn(expected, links)
        self.assertEqual(built["order"], ["c1", "c2", "c3"])
        self.assertEqual(built["prerequisites"], [["Cell", ["c1"], "outside"]])
        self.assertEqual(built["chapter"]["content_types"], TYPES.version)
        self.assertEqual(len(built["sha256"]), 64)
        self.assertEqual(nk.build(small_chapter())["sha256"], built["sha256"])          # same map, same naksha
        changed = small_chapter()
        changed["items"]["p002-i1"]["content"] = "Cells divide by meiosis."
        self.assertNotEqual(nk.build(changed)["sha256"], built["sha256"])

    def test_a_map_from_before_task_045_is_converted(self):
        built = nk.build(small_chapter("old"))
        rows = {r[0]: r for r in built["items"]}
        self.assertEqual(rows["p001-i2"][1], "facts_numbers")                    # fact
        self.assertEqual(rows["p001-i1"][1], "definition")                       # example -> its concept's type

    def test_slices_carry_own_items_and_one_row_per_related_concept(self):
        built = nk.build(small_chapter())
        rows = nk.slice_rows(built, ["p001-i4"])
        ids = [r[0] for r in rows]
        self.assertEqual(ids[:2], ["p001-i4", "p001-i3"])                        # own item, then the table it is part of
        self.assertIn("c2", ids)                                                 # its concept
        self.assertTrue({"c1", "c3"} <= set(ids))                                # prerequisite and cause/compare concepts
        self.assertNotIn("p002-i1", ids)                                         # never the related concepts' items
        self.assertTrue(all(len(r) == 4 and all(isinstance(x, str) for x in r) for r in rows))
        self.assertEqual(nk.concept_slice(built)[1], ["c2", "classification", "1", "Kinds of tissue"])
        size = nk.size(built)
        self.assertEqual(size["items"], 6)
        self.assertEqual(size["tokens_estimate"], round(size["chars"] / nk.CHARS_PER_TOKEN))


# ---------------------------------------------------------------- task cards

class TaskCards(unittest.TestCase):
    def setUp(self):
        self.prefix, self.review = page_prefixes(COURSE, BOOK)

    def card(self, page=None, **extra):
        page = page or page_of(*TISSUE_PAGE)
        step = page_step(COURSE, page, page_count=14, rulebook=BOOK)
        return dict(step.card, **extra), step

    def test_the_prefix_is_the_same_for_every_page_and_holds_nothing_per_page(self):
        one = page_step(COURSE, page_of(*TISSUE_PAGE, number=3), page_count=14, rulebook=BOOK)
        two = page_step(COURSE, page_of("Connective Tissues", "• Connects body parts", number=4), page_count=14, rulebook=BOOK)
        self.assertEqual(one.system, two.system)
        self.assertEqual(one.card["prefix"]["sha256"], cards.sha256(one.system))
        self.assertEqual(one.card["prefix"], two.card["prefix"])
        self.assertNotIn("Page 3", one.system)
        self.assertNotIn("p0003", one.system)
        self.assertTrue(one.system.startswith("BIE task prefix understand.read_page/2 · rulebook " + BOOK.version))
        for rule in BOOK.for_section("understand"):
            self.assertIn(f"[{rule.id}]", one.system)
        self.assertIn("Required questions: how (kaise), when (kab)", one.system)
        other = page_prefixes(Course("Other", "History", "Class 8", "CBSE", "English"), BOOK)[0]
        self.assertNotEqual(other.sha256, self.prefix.sha256)
        self.assertNotEqual(self.review.sha256, self.prefix.sha256)

    def test_the_page_card_names_proposals_coverage_and_boilerplate(self):
        card, step = self.card()
        self.assertEqual(card["card_id"], "understand.read_page@10-tissues-and-its-types/page-003")
        self.assertEqual(card["parts"][0]["type"], "classification")
        self.assertEqual(card["parts"][0]["item_ids"], ["p0003-b0002", "p0003-b0003", "p0003-b0004"])
        self.assertEqual(card["parts"][0]["questions"], ["which", "difference"])
        self.assertIn("pattern 'types of'", card["parts"][0]["focus"])
        self.assertEqual({s["item_id"]: s["reason"] for s in card["coverage"]["may_skip"]}, {"p0003-b0006": "page number"})
        self.assertEqual(card["coverage"]["must_cover"], [f"p0003-b000{n}" for n in range(1, 6)])
        self.assertEqual(card["source"]["page_images"][0]["page"], 3)
        self.assertEqual(cards.read_card(text_of(step.user)), card)
        self.assertEqual(cards.check(card, prefix=self.prefix, rulebook=BOOK, known_ids=set(card["coverage"]["must_cover"])
                                     | {"p0003-b0006", "p0003-image"}), [])

    def test_running_headers_are_proposed_as_skippable(self):
        previous, page = page_of("Science and Technology", "Cells.", number=2), page_of(*TISSUE_PAGE)
        self.assertEqual(likely_boilerplate(page, (previous, None))["p0003-b0001"],
                         "running header (the same first line as the next or previous page)")

    def test_card_checks_catch_bad_cards(self):
        card, _ = self.card()
        known = set(card["coverage"]["must_cover"]) | {"p0003-b0006", "p0003-image"}
        bad = copy.deepcopy(card)
        bad["prefix"]["sha256"] = "0" * 64
        bad["task"] = "write_script"
        bad["rules"].append("S6-01")
        bad["parts"][0]["questions"] = ["what"]
        bad["coverage"]["must_cover"].append("p0099-b0001")
        problems = cards.check(bad, prefix=self.prefix, rulebook=BOOK, known_ids=known)
        for fragment in ("card prefix does not match", "task write_script does not belong to section understand",
                         "['S6-01'] are not locked rules", "a classification part must ask ['which', 'difference']",
                         "ids not in the chapter: ['p0099-b0001']"):
            self.assertTrue(any(fragment in p for p in problems), fragment)
        self.assertTrue(cards.check(dict(card, parts=[]), prefix=self.prefix, rulebook=BOOK)[0].startswith("card does not match"))
        with self.assertRaises(cards.CardError):
            cards.require_valid(bad, prefix=self.prefix, rulebook=BOOK, known_ids=known)

    def test_must_cover_is_checked_both_ways(self):
        card, _ = self.card()
        must = card["coverage"]["must_cover"]
        self.assertEqual(cards.coverage_problems(card, must + ["p0003-b0006"]), [])
        problems = cards.coverage_problems(card, must[1:] + ["p0003-b0099"], rule="S1-02")
        self.assertIn("1 ids of must_cover are not claimed", problems[0])
        self.assertIn("(S1-02): p0003-b0001", problems[0])
        self.assertIn("p0003-b0099", problems[1])

    def test_a_card_id_is_used_once_per_run(self):
        card, _ = self.card()
        book = cards.CardBook()
        book.add(card)
        self.assertEqual(book.prefixes, {"understand.read_page/2": self.prefix.sha256})
        with self.assertRaises(cards.CardError):
            book.add(card)

    def test_the_runner_refuses_a_card_whose_prefix_is_not_sent(self):
        _, step = self.card()
        step.system = step.system + " changed"
        runner = SectionRunner(gateway(), maker="anthropic", reviewer="openai", rulebook=BOOK)
        with self.assertRaises(ValueError):
            runner.run(step)


# ---------------------------------------------------------------- Section 1 on the card

class Disagreeing(BrainFakeClient):
    """Round 1 types the list lines as facts without a reason; the patch keeps them and gives the reason."""

    def _respond(self, model, messages, schema):
        props = (schema or {}).get("properties", {})
        if "items" in props and "replace_items" not in props:
            raw = super()._respond(model, messages, schema)
            value = json.loads(raw["content"])
            for entry in value["items"]:
                if entry["block_ids"] in (["p0003-b0003"], ["p0003-b0004"]):
                    entry["content_type"] = "facts_numbers"
                    entry["teacher_understanding"] = [dict(q, basis="book") for q in qa("what", "evidence", "why")]
            self.first = value
            return dict(raw, content=json.dumps(value, ensure_ascii=False))
        if "replace_items" in props:
            fixed = [dict(i, type_note="each numbered line names one kind and its job; the classification is the line above")
                     for i in self.first["items"] if i["content_type"] == "facts_numbers"]
            self.calls.append({"model": model, "kind": "patch"})
            return {"content": json.dumps({"notes": self.first["notes"], "replace_items": fixed, "remove_item_ids": [],
                                           "boilerplate_block_ids": self.first["boilerplate_block_ids"],
                                           "text_image_disagreements": []}, ensure_ascii=False),
                    "finish_reason": "stop", "model": "fake", "usage": {"input_tokens": 10, "output_tokens": 10}}
        return super()._respond(model, messages, schema)


class SectionOneOnTheCard(unittest.TestCase):
    def test_required_questions_none_type_and_numbers(self):
        page = page_of("Cells divide in steps.", "The heart beats 72 times per minute.", "Leaves.", number=1)
        value = {"notes": {}, "page_summary": "", "boilerplate_block_ids": [], "text_image_disagreements": [], "items": [
            item("i1", ["p0001-b0001"], "process", "how", "why"),
            item("i2", ["p0001-b0002"], "facts_numbers", "what", "evidence", "why", content="The heart beats 75 times per minute."),
            item("i3", ["p0001-b0003"], "none", "what", "why")]}
        problems = check_page(value, page)
        self.assertTrue(any("a process item must answer the required questions ['when'] (kab)" in p for p in problems))
        self.assertTrue(any("item i2: the numbers ['75'] are not in its blocks" in p for p in problems))
        self.assertTrue(any("item i3: a teachable item needs one of BIE's nine content types" in p for p in problems))
        value["items"][1]["content"] = "The heart beats 72 times per minute."
        value["items"][0]["teacher_understanding"] = qa("how", "when", "why")
        value["items"][2]["content_type"] = "structure"
        value["items"][2]["teacher_understanding"] = qa("what", "where", "why")
        self.assertEqual(check_page(value, page), [])

    def test_an_unexplained_type_difference_goes_back_and_an_explained_one_passes(self):
        page = page_of(*TISSUE_PAGE)
        maker = Disagreeing("anthropic")
        with tempfile.TemporaryDirectory() as folder:
            runner = SectionRunner(gateway(maker), maker="anthropic", reviewer="openai", rulebook=BOOK, records_dir=folder)
            result = runner.run(page_step(COURSE, page, page_count=14, rulebook=BOOK))
            self.assertTrue(result.passed)
            self.assertEqual(len(result.rounds), 2)
            first = result.rounds[0]
            self.assertEqual(len([p for p in first["code_problems"] if "BIE's code proposes classification" in p]), 2)
            self.assertEqual(first["observed"]["type_summary"]["disagree"], 2)
            self.assertEqual(result.rounds[1]["observed"]["type_summary"]["explained"], 2)
            record = json.loads(Path(result.record_path).read_text(encoding="utf-8"))
            self.assertEqual(record["card"]["card_id"], "understand.read_page@10-tissues-and-its-types/page-003")
            self.assertEqual(record["prefix_sha256"], record["card"]["prefix"]["sha256"])
            self.assertEqual(len(record["review_prefix_sha256"]), 64)
            self.assertTrue(any(r["status"] == "explained" and r["type_note"] for r in record["rounds"][1]["observed"]["type_check"]))

    def test_old_engines_check_the_chapter_map(self):
        chapter = small_chapter()
        items, value = chapter["items"], copy.deepcopy(chapter["map"])
        problems, observed = engines.map_checks(value, items)
        self.assertEqual(problems, [])
        self.assertEqual(observed["ki_coverage"]["coverage"], 1.0)
        value["relations"] += [{"from_concept": "c1", "relation": "depends_on", "to_concept": "c2", "note": ""}]
        self.assertIn("prerequisites go in a circle", engines.map_checks(value, items)[0][0])
        value = copy.deepcopy(chapter["map"])
        value["teaching_order"] = ["c2", "c1", "c3"]
        problems = engines.map_checks(value, items)[0]
        self.assertIn("teaching_order teaches c2 before its prerequisite c1", problems[0])
        self.assertIn("an order that keeps yours where it can: c1, c2, c3", problems[0])
        value = copy.deepcopy(chapter["map"])
        value["relations"] += [{"from_concept": "c2", "relation": "causes", "to_concept": "c3", "note": ""},
                               {"from_concept": "c3", "relation": "depends_on", "to_concept": "c1", "note": ""},
                               {"from_concept": "c2", "relation": "depends_on", "to_concept": "c3", "note": ""}]
        problems, observed = engines.map_checks(value, items)
        self.assertTrue(any("cause and effect go in a circle" in p for p in problems))
        self.assertIn("c2 depends_on c1", observed["redundant_prerequisite_links"])

    def test_dated_links_must_not_go_back_in_time(self):
        items = {"a": {"content": "The Revolt of 1857 began at Meerut.", "teachable": True},
                 "b": {"content": "The Jallianwala Bagh massacre of 1919.", "teachable": True},
                 "c": {"content": "Ashoka ruled from 268 BC.", "teachable": True}}
        value = {"concepts": [{"concept_id": "x", "item_ids": ["a"]}, {"concept_id": "y", "item_ids": ["b"]},
                              {"concept_id": "z", "item_ids": ["c"]}],
                 "relations": [{"from_concept": "y", "relation": "sequence_next", "to_concept": "x"},
                               {"from_concept": "z", "relation": "sequence_next", "to_concept": "x"}], "teaching_order": ["z", "x", "y"]}
        problems = engines.map_checks(value, items)[0]
        self.assertEqual(len(problems), 1)
        self.assertIn("y sequence_next x, but y is dated 1919 and x 1857", problems[0])

    def test_connect_step_runs_on_a_card_with_engine_checks(self):
        chapter = small_chapter()
        step = connect_step(COURSE, chapter["items"], rulebook=BOOK)
        self.assertEqual(step.card["task"], "build_chapter_map")
        self.assertEqual(sorted(step.card["coverage"]["must_cover"]),
                         sorted(i for i, it in chapter["items"].items() if it["teachable"]))
        bad = copy.deepcopy(chapter["map"])
        bad["relations"].append({"from_concept": "c1", "relation": "depends_on", "to_concept": "c2", "note": ""})
        self.assertTrue(any("prerequisites go in a circle" in p for p in step.check(bad)))
        self.assertIn("ki_coverage", step.observe(chapter["map"]))
        self.assertIn("p002-i1 | 2 | paragraph | process | teach | high | Cells divide by mitosis in steps.", text_of(step.user))


# ---------------------------------------------------------------- the retired producers

class Retired(unittest.TestCase):
    def test_every_engine_has_a_decision_and_a_reason(self):
        self.assertEqual([d["engine"] for d in engines.DECISIONS], ["KI", "PR", "RE", "PED"])
        for decision in engines.DECISIONS:
            self.assertTrue(decision["decision"] and decision["reason"] and decision["used_as_checks"])
        self.assertEqual(engines.RETIRED_MODULES, ("bie.productization.candidates", "bie.productization.pr_reasoning",
                                                   "bie.productization.pedagogy_plan", "bie.productization.pedagogy_slice"))

    def test_no_brain_code_calls_a_retired_producer_and_no_file_was_deleted(self):
        for module in engines.RETIRED_MODULES:
            self.assertTrue((ROOT / (module.replace(".", "/") + ".py")).exists(), module)   # retired, never deleted
        sources = list((ROOT / "bie/brain").rglob("*.py")) + [ROOT / "tools/run_brain.py"]
        for path in sources:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    names = [node.module] + [f"{node.module}.{a.name}" for a in node.names]
                for name in names:
                    self.assertFalse(any(name == m or name.startswith(m + ".") for m in engines.RETIRED_MODULES),
                                     f"{path.relative_to(ROOT)} imports retired {name}")


# ---------------------------------------------------------------- Section 2 on the card

def lesson_plan(chapter):
    return {"videos": [{"video_id": "v1", "title": "Tissue", "goal": "", "concept_ids": ["c1", "c2"], "prerequisites_taught": ["Cell"],
                        "opening_hook": "", "story_or_analogy": "", "estimated_minutes": 2, "why_this_unit": ""},
                       {"video_id": "v2", "title": "Division", "goal": "", "concept_ids": ["c3"], "prerequisites_taught": [],
                        "opening_hook": "", "story_or_analogy": "", "estimated_minutes": 1, "why_this_unit": ""}]}


def beat(bid, part="", step=0, covers=(), answers=(), say=None):
    return {"beat_id": bid, "part_id": part, "step": step, "purpose": "explain",
            "say": say or "ये बात ध्यान से समझिए, ये tissue का हिस्सा है और exam में आती है।", "covers_item_ids": list(covers),
            "answers": list(answers), "on_screen": "", "basis": "book"}


class SectionTwoOnTheCard(unittest.TestCase):
    def setUp(self):
        self.chapter = small_chapter()
        self.naksha = nk.build(self.chapter)
        self.plan = lesson_plan(self.chapter)
        self.prefix, _ = script_prefixes(COURSE, BOOK)
        self.card = script_card(COURSE, self.chapter, self.naksha, self.plan, self.plan["videos"][0], rulebook=BOOK,
                                prefix=self.prefix)

    def good(self):
        beats = [beat("b0")]
        for part in self.card["parts"]:
            for n in range(1, len(TYPES.pattern(part["type"])) + 1):
                ids = part["item_ids"] if n == 1 else []
                answers = [f"{i}#q{k}" for i in ids for k in range(1, 4)]
                beats.append(beat(f"b{len(beats)}", part["part_id"], n, ids, answers))
        beats.append(beat("b-end"))
        frames = [{"part_id": p["part_id"], "frame": {k: f"{k} of this part" for k in FRAME}} for p in self.card["parts"]]
        return {"notes": {}, "title": "Tissue", "parts": frames, "beats": beats}

    def test_the_plan_card_carries_concepts_only(self):
        prefix = _prefix(COURSE, BOOK, "plan_videos", PLAN_SCHEMA_ID, PLAN_SCHEMA, PLAN_ROLE, PLAN_HOW)
        card = plan_card(COURSE, self.chapter, self.naksha, rulebook=BOOK, prefix=prefix)
        self.assertEqual([p["part_id"] for p in card["parts"]], ["c1", "c2", "c3"])
        self.assertEqual(card["coverage"]["must_cover"], ["c1", "c2", "c3"])
        self.assertEqual([r[0] for r in card["context"]["map_slice"]], ["c1", "c2", "c3"])
        self.assertIn("Teaching pattern: 1) the result first", prefix.text)

    def test_the_script_card_groups_items_by_type_with_their_questions(self):
        parts = {p["part_id"]: p for p in self.card["parts"]}
        self.assertEqual(sorted(parts), ["c1.1", "c1.2", "c2.1", "c2.2"])
        self.assertEqual(parts["c1.2"]["type"], "facts_numbers")
        self.assertEqual(parts["c1.2"]["questions"][:2], ["what", "evidence"])
        self.assertEqual(self.card["coverage"]["must_cover"], ["p001-i1", "p001-i2", "p001-i3", "p001-i4"])
        self.assertEqual(self.card["context"]["after"], "Division")
        self.assertIn("c3", [r[0] for r in self.card["context"]["map_slice"]])   # the concept it contrasts with

    def test_a_good_script_passes_every_check(self):
        video = self.plan["videos"][0]
        self.assertEqual(check_script(self.good(), self.chapter, video, "Hinglish", self.card), [])

    def test_frame_pattern_coverage_and_spoken_style(self):
        video = self.plan["videos"][0]
        value = self.good()
        value["parts"] = value["parts"][1:]
        value["parts"][0]["frame"]["how"] = ""
        value["beats"] = [b for b in value["beats"] if not (b["part_id"] == "c2.1" and b["step"] == 3)]
        value["beats"][1]["covers_item_ids"] = ["p001-i1", "p009-i9"]
        value["beats"][2]["step"] = 9
        value["beats"][3]["say"] = "ये बात २ बार समझिए। " + "और " * 45 + "समझिए।"
        value["beats"] = [b for b in value["beats"] if "p001-i4" not in b["covers_item_ids"]]
        problems = check_script(value, self.chapter, video, "Hinglish", self.card)
        for fragment in ("part c1.1: the universal frame is missing", "frame fields ['how'] are empty",
                         "part c2.1 (classification): teaching-pattern steps not taught: 3) each kind",
                         "is not a step of the", "item 'p009-i9' is not an item of this video",
                         "ids of must_cover are not claimed in beats[].covers_item_ids (S2-02): p001-i4",
                         "write numbers in Devanagari digits", "a sentence longer than 40 words"):
            self.assertTrue(any(fragment in p for p in problems), fragment)

    def test_a_process_part_cannot_skip_how_with_na(self):
        plan = self.plan
        card = script_card(COURSE, self.chapter, self.naksha, plan, plan["videos"][1], rulebook=BOOK, prefix=self.prefix)
        part = card["parts"][0]
        self.assertEqual(part["type"], "process")
        value = {"parts": [{"part_id": part["part_id"], "frame": dict({k: "x" for k in FRAME}, how="n/a: nothing")}], "beats": []}
        from bie.brain.lesson import frame_problems
        self.assertTrue(any("a process part must answer ['how'] in its frame" in p for p in frame_problems(value, card)[0]))

    def test_ped_checks_load_and_length(self):
        heavy = beat("b1", covers=["a", "b", "c", "d", "e"])
        problems, observed = engines.script_checks([heavy], ["a", "b", "c", "d", "e"], planned_minutes=10)
        self.assertTrue(any("beat b1 is too heavy for one breath" in p for p in problems))
        self.assertTrue(any("nothing may be compressed away" in p for p in problems))
        self.assertEqual(observed["objective_coverage"]["coverage"], 1.0)
        problems, _ = engines.plan_checks([{"video_id": "v1", "concept_ids": ["c1"], "prerequisites_taught": []}], [],
                                          [{"name": "Cell"}])
        self.assertIn("prerequisite 'Cell' is taught in no video", problems[0])

    def test_spoken_hinglish(self):
        self.assertEqual(spoken_problems([beat("b1"), beat("b2"), beat("b3")], "Hinglish"), [])
        english = [beat(f"b{n}", say="This is English only.") for n in range(5)]
        self.assertIn("written in Devanagari", spoken_problems(english, "Hinglish")[0])

    def test_patch_replaces_frames_and_beats(self):
        previous = self.good()
        patched = apply_script_patch(previous, {"notes": {}, "replace_parts": [{"part_id": "c1.1", "frame": {k: "new" for k in FRAME}}],
                                                "replace_beats": [], "insert_beats": [{"after_beat_id": "b0", "beat": beat("b0a")}],
                                                "remove_beat_ids": ["b-end"]})
        self.assertEqual(patched["parts"][0]["frame"]["how"], "new")
        self.assertEqual([b["beat_id"] for b in patched["beats"]][:2], ["b0", "b0a"])
        self.assertNotIn("b-end", [b["beat_id"] for b in patched["beats"]])



# ---------------------------------------------------------------- mixed-script narration (Task 045b)

class MixedScript(unittest.TestCase):
    def test_simple_words_inflections_and_spelling_variants(self):
        from bie.brain import hinglish
        simple = hinglish.load()
        self.assertTrue(simple.version)
        for word in ("पढ़ेंगे", "पढेंगे", "समझते", "हमने", "आँख", "आंख", "आएगा", "बच्चों", "जरा", "ज़रा"):
            self.assertTrue(simple.is_simple(word), word)
        for word in ("ऊतक", "सतह", "कोशिकाएँ", "विभाजन"):
            self.assertFalse(simple.is_simple(word), word)

    def test_the_check_wants_brackets_after_difficult_words_only(self):
        from bie.brain import hinglish
        self.assertEqual(hinglish.difficult_words("आज हम tissue के बारे में पढ़ेंगे।"), [])
        self.assertEqual(hinglish.difficult_words("पत्ती की सतह (surface) पर cells होते हैं।"), [])
        self.assertEqual(hinglish.difficult_words("पत्ती की सतह पर ऊतक होते हैं।"), ["सतह", "ऊतक"])
        self.assertEqual(hinglish.bracket_problems("सतह (surface) ठीक है"), [])
        self.assertTrue(hinglish.bracket_problems("सतह (सतह)")[0].endswith("in Roman letters"))
        self.assertEqual(hinglish.roman_hindi("ye tissue hai aur cells"), ["aur", "hai"])
        self.assertEqual(hinglish.roman_hindi("Mitosis is important to cells"), [])     # English is never flagged

    def test_voice_says_yani_and_subtitles_keep_the_bracket(self):
        from bie.brain import hinglish
        say = "पत्ती की सतह (surface) पर cells होते हैं।"
        self.assertEqual(hinglish.voice_text(say), "पत्ती की सतह, यानी surface पर cells होते हैं।")
        self.assertEqual(hinglish.subtitle_text(say), say)

    def test_spoken_problems_enforce_s2_04_without_forcing_scripts(self):
        good = [beat("b1", say="आज हम tissue के बारे में पढ़ेंगे।"), beat("b2", say="पत्ती की सतह (surface) देखिए।"),
                beat("b3", say="Epidermis एक layer है।")]
        self.assertEqual(spoken_problems(good, "Hinglish"), [])
        bad = [beat("b1", say="पत्ती की सतह पर ऊतक है।"), beat("b2", say="ये tissue hai aur ये layer है।"),
               beat("b3", say="ये सतह (सतह) है।")]
        problems = spoken_problems(bad, "Hinglish")
        self.assertTrue(any("beat b1: the Hindi words ['सतह', 'ऊतक'] are not simple" in p for p in problems))
        self.assertTrue(any("beat b2: the Hindi words ['aur', 'hai'] are written in Roman" in p for p in problems))
        self.assertTrue(any("beat b3: (सतह) must hold the English word in Roman letters" in p for p in problems))

    def test_rule_and_word_list_are_in_the_rulebook_and_the_prefix(self):
        book = rulebook.load()
        self.assertIn("simple_hindi@", book.version)
        s204 = next(r for r in book.rules if r.id == "S2-04")
        self.assertIn("सतह (surface)", s204.rule)
        self.assertIn("यानी", s204.rule)
        prefix, _ = script_prefixes(COURSE, BOOK)
        self.assertIn("Simple everyday Hindi words (list", prefix.text)
        self.assertIn("सतह, यानी surface", prefix.text)


# ---------------------------------------------------------------- the whole chain offline

class Chain(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        lines = [["There are mainly four different types of tissues present in our body.", "1. Epithelial- provides covering",
                  "2. Muscular- helps in movement", "Collagen fibres are made up of fibrous protein."],
                 [], ["Cells divide by mitosis.", "The heart beats 72 times per minute."]]
        self.pdf = Path(self.tmp.name, "chapter.pdf")
        self.pdf.write_bytes(positioned_text_pdf([[(72, 720 - i * 20, t) for i, t in enumerate(page)] for page in lines]))

    def args(self, out, *extra):
        return ["--fake", "--section", "chain", "--source", str(self.pdf), "--out", str(Path(self.tmp.name, out)), "--workers", "1",
                "--course", "title=10. Tissues and Its Types;subject=Biology;learners=UPSC;exam=UPSC;language=Hinglish", "--max-inr", "100000",
                *extra]

    def read(self, out, name):
        return json.loads(Path(self.tmp.name, out, name).read_text(encoding="utf-8"))

    def test_chain_on_cards_writes_naksha_types_frames_and_records(self):
        code, _ = run(self.args("ok"))
        self.assertEqual(code, 0)
        summary = self.read("ok", "SUMMARY.json")
        self.assertEqual(summary["status"], "ok")
        chapter = self.read("ok", "chapter_map.json")
        self.assertEqual(chapter["schema"], "bie.brain.chapter-map/2")
        self.assertEqual(chapter["map_status"], "passed")
        self.assertEqual(chapter["type_check"]["summary"]["agree"], 4)      # the classification line, its list, "made up of"
        naksha = json.loads(Path(self.tmp.name, "ok", "naksha.json").read_text(encoding="utf-8"))
        self.assertEqual(naksha["sha256"], chapter["naksha"]["sha256"])
        self.assertEqual(naksha["naksha"], nk.SCHEMA)
        self.assertIn("Naksha (the compact map", Path(self.tmp.name, "ok", "MAP.md").read_text(encoding="utf-8"))
        self.assertIn("## Content types: BIE's code and the AI", Path(self.tmp.name, "ok", "MAP.md").read_text(encoding="utf-8"))
        records = {p.name: json.loads(p.read_text(encoding="utf-8")) for p in Path(self.tmp.name, "ok", "records").glob("*.json")}
        page_prefixes_seen = {r["prefix_sha256"] for name, r in records.items() if name.startswith("understand--")}
        self.assertEqual(len(page_prefixes_seen), 1)                 # one cacheable prefix for every page
        self.assertEqual(records["lesson--script-v1.json"]["card"]["task"], "write_script")
        self.assertIn("observed", records["lesson--script-v1.json"]["rounds"][0])
        lesson = self.read("ok", "lesson_plan.json")
        self.assertEqual(lesson["schema"], "bie.brain.lesson/2")
        self.assertEqual(lesson["naksha_sha256"], naksha["sha256"])
        first = lesson["videos"][0]
        self.assertTrue(first["parts"] and first["card_parts"])
        self.assertTrue(all(b.get("part_id") is not None and "step" in b for b in first["beats"]))
        script = Path(self.tmp.name, "ok", "SCRIPT.md").read_text(encoding="utf-8")
        self.assertIn("### Part c1.1 · classification", script)
        self.assertIn("step 1: the basis of division first", script)
        self.assertEqual(summary["lesson_quality"]["videos_passed"], summary["lesson_quality"]["videos"])

    def test_resume_reuses_only_pages_that_pass_todays_checks(self):
        code, _ = run(self.args("first", "--section", "understand"))
        self.assertEqual(code, 0)
        old = self.read("first", "chapter_map.json")
        for iid, entry in old["items"].items():          # make it look like a run from before Task 045
            if entry["page"] == 1:
                entry["content_type"] = "fact" if entry["content_type"] == "classification" else entry["content_type"]
        with tempfile.TemporaryDirectory() as folder:
            runner = SectionRunner(gateway(), maker="anthropic", reviewer="openai", rulebook=BOOK, records_dir=Path(folder, "records"))
            chapter = run_chapter(self.pdf.read_bytes(), COURSE, runner, folder, workers=1, previous_chapter=old)
        pages = {p["page"]: p for p in chapter["pages"]}
        self.assertFalse(pages[1]["reused"])                 # converted "fact" items lack the required evidence question
        self.assertTrue(pages[1]["reuse_refused"])
        self.assertTrue(pages[2]["reused"] and pages[3]["reused"])
        self.assertEqual(chapter["quality"]["pages_reused"], 2)

    def test_same_model_checker_is_the_weakest_check_and_marked(self):
        code, _ = run(self.args("same", "--section", "understand", "--maker", "google", "--reviewer", "google",
                                "--reviewer-model", "same", "--pages", "1"))
        self.assertEqual(code, 0)
        summary = self.read("same", "SUMMARY.json")
        self.assertEqual(summary["reviewer_independence"], "same_model_temporary")
        self.assertEqual(summary["models"], {"google": "fake-google", "google-checker": "fake-google"})
        self.assertIn("kamzor jaanch", Path(self.tmp.name, "same", "MAP.md").read_text(encoding="utf-8"))
        with self.assertRaises(SystemExit):
            run(self.args("x", "--maker", "google", "--reviewer", "openai", "--reviewer-model", "same"))

    def test_a_lesson_from_a_map_made_before_task_045_still_runs(self):
        chapter = small_chapter("old")
        with tempfile.TemporaryDirectory() as folder:
            from bie.brain.lesson import run_lesson
            runner = SectionRunner(gateway(), maker="anthropic", reviewer="openai", rulebook=BOOK, records_dir=Path(folder, "r"))
            lesson = run_lesson(chapter, COURSE, runner, folder, workers=1)
        self.assertTrue(lesson["quality"]["plan_passed"])
        self.assertEqual(lesson["quality"]["videos_passed"], lesson["quality"]["videos"])



# ---------------------------------------------------------------- resume and readable pages (Task 045 PR B)

class LessonResumeAndPages(unittest.TestCase):
    def run_lesson(self, folder, previous=None, chapter=None):
        from bie.brain.lesson import run_lesson
        maker, reviewer = BrainFakeClient("anthropic"), BrainFakeClient("openai")
        runner = SectionRunner(gateway(maker, reviewer), maker="anthropic", reviewer="openai", rulebook=BOOK,
                               records_dir=Path(folder, "records"))
        lesson = run_lesson(chapter or small_chapter(), COURSE, runner, folder, workers=1, previous_lesson=previous)
        return lesson, maker.calls + reviewer.calls

    def test_a_finished_lesson_is_reused_without_any_call(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            lesson, calls = self.run_lesson(first)
            self.assertTrue(calls)
            self.assertEqual(lesson["quality"]["videos_reused"], 0)
            again, calls = self.run_lesson(second, previous=lesson)
            self.assertEqual(calls, [])
            self.assertTrue(again["plan_reused"])
            self.assertEqual(again["quality"]["videos_reused"], again["quality"]["videos"])
            self.assertEqual(again["quality"]["videos_passed"], again["quality"]["videos"])
            self.assertTrue(all(v["reused"] and v["record"] for v in again["videos"]))
            self.assertEqual([b["say"] for b in again["videos"][0]["beats"]], [b["say"] for b in lesson["videos"][0]["beats"]])
            self.assertIn("(reused)", Path(second, "SCRIPT.md").read_text(encoding="utf-8"))

    def test_only_what_did_not_pass_or_fails_today_runs_again(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            lesson, _ = self.run_lesson(first)
            previous = copy.deepcopy(lesson)
            previous["videos"][0]["status"] = "stopped"                       # stopped by the cap or the plan limit
            previous["videos"][1]["beats"] = previous["videos"][1]["beats"][:1]   # would fail today's coverage check
            again, calls = self.run_lesson(second, previous=previous)
            self.assertTrue(again["plan_reused"])
            self.assertEqual([v["reused"] for v in again["videos"]], [False, False, True])
            self.assertTrue(calls)
            self.assertTrue(any("v2 fails today's checks" in n for n in again["resume_notes"]))
            self.assertEqual(again["quality"]["videos_passed"], 3)

    def test_nothing_is_reused_when_the_chapter_map_changed(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            lesson, _ = self.run_lesson(first)
            changed = small_chapter()
            changed["items"]["p002-i1"]["content"] = "Cells divide by meiosis in steps."
            again, calls = self.run_lesson(second, previous=lesson, chapter=changed)
            self.assertFalse(again["plan_reused"])
            self.assertEqual(again["quality"]["videos_reused"], 0)
            self.assertIn("the chapter map changed", again["resume_notes"][0])

    def test_one_readable_page_per_video(self):
        with tempfile.TemporaryDirectory() as folder:
            lesson, _ = self.run_lesson(folder)
            first = lesson["videos"][0]
            page = Path(folder, "scripts", "v1.md").read_text(encoding="utf-8")
            self.assertTrue(page.startswith(f"# {first['title']}"))
            self.assertIn(f"## v1 · {first['title']} · passed", page)
            self.assertIn("### Part c1.1 · definition", page)
            self.assertEqual(len(list(Path(folder, "scripts").glob("*.md"))), len(lesson["videos"]))
            self.assertIn(f"| v2 | {lesson['videos'][1]['title']} | passed |", Path(folder, "SCRIPT.md").read_text(encoding="utf-8"))


class ReadablePagesAndRunResume(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        lines = [["There are mainly four different types of tissues present in our body.", "1. Epithelial- provides covering"],
                 ["Cells divide by mitosis.", "The heart beats 72 times per minute."]]
        self.pdf = Path(self.tmp.name, "chapter.pdf")
        self.pdf.write_bytes(positioned_text_pdf([[(72, 720 - i * 20, t) for i, t in enumerate(page)] for page in lines]))

    def args(self, out, *extra):
        return ["--fake", "--out", str(Path(self.tmp.name, out)), "--workers", "1", "--max-inr", "100000",
                "--course", "title=T;subject=Biology;learners=UPSC;exam=UPSC;language=Hinglish", *extra]

    def test_map_is_short_and_pages_hold_every_item(self):
        code, _ = run(self.args("u", "--section", "understand", "--source", str(self.pdf)))
        self.assertEqual(code, 0)
        text = Path(self.tmp.name, "u", "MAP.md").read_text(encoding="utf-8")
        self.assertIn("| Page | Result | Rounds | Items | Cost |", text)
        self.assertIn("| 1 | passed | 1 |", text)
        self.assertNotIn("p001-i1** ·", text)
        self.assertIn("p001-i1** ·", Path(self.tmp.name, "u", "PAGES.md").read_text(encoding="utf-8"))

    def test_lesson_resume_from_an_earlier_run_folder(self):
        run(self.args("u", "--section", "understand", "--source", str(self.pdf)))
        chapter_map = str(Path(self.tmp.name, "u", "chapter_map.json"))
        code, _ = run(self.args("l1", "--section", "lesson", "--chapter-map", chapter_map))
        self.assertEqual(code, 0)
        code, _ = run(self.args("l2", "--section", "lesson", "--chapter-map", chapter_map,
                                "--resume-from", str(Path(self.tmp.name, "l1"))))
        self.assertEqual(code, 0)
        summary = json.loads(Path(self.tmp.name, "l2", "SUMMARY.json").read_text(encoding="utf-8"))
        self.assertTrue(summary["resume"]["plan_reused"])
        self.assertEqual(summary["resume"]["scripts_reused"], summary["lesson_quality"]["videos"])
        self.assertEqual(set(summary["cost"]["sections"]), {"preflight"})         # no lesson call was paid again

    def test_render_run_rebuilds_the_readable_pages_of_a_folder(self):
        import render_run
        run(self.args("u", "--section", "chain", "--source", str(self.pdf)))
        written = render_run.render(Path(self.tmp.name, "u"), Path(self.tmp.name, "u", "readable"))
        self.assertEqual(written[:3], ["MAP.md", "PAGES.md", "SCRIPT.md"])
        self.assertTrue(Path(self.tmp.name, "u", "readable", "scripts", "v1.md").exists())
        rate = json.loads(Path(self.tmp.name, "u", "SUMMARY.json").read_text(encoding="utf-8"))["cost"]["usd_inr"]
        chapter = json.loads(Path(self.tmp.name, "u", "chapter_map.json").read_text(encoding="utf-8"))
        self.assertIn(f"- Estimated cost: ₹{chapter['cost_usd'] * rate:.2f} (",
                      Path(self.tmp.name, "u", "readable", "MAP.md").read_text(encoding="utf-8"))   # rupees for Navin
        self.assertIn("estimated cost ₹", Path(self.tmp.name, "u", "readable", "SCRIPT.md").read_text(encoding="utf-8"))
        self.assertIn("- Estimated cost: $", Path(self.tmp.name, "u", "MAP.md").read_text(encoding="utf-8"))  # the run's own page
        with self.assertRaises(SystemExit):
            render_run.main([str(Path(self.tmp.name, "empty"))])


if __name__ == "__main__":
    unittest.main()
