"""Section 1 · Understanding the book.

Each page is read with two eyes (native text blocks and the page image) into items with page
locations, and every teachable item is understood through a teacher's questions (what, where, how,
why, compare, difference ... and deeper "why" and "how" on the answers). Then one chapter step
connects the items into concepts, relations, prerequisites to teach, resolved cross-references and
a teaching order. Every step goes through ``SectionRunner``: code checks, an independent reviewer
on another provider, bounded remakes and a full process record.

Since Task 045 both steps run on task cards (``bie/brain/cards.py``): a fixed, cacheable prefix and a compact
card. Before the maker reads a page, BIE's code proposes a content type per block (``content_types.py``);
the maker uses BIE's nine type ids, answers at least the required questions of each item's type, and gives a
``type_note`` when it chooses another type than the code; every difference is recorded. The chapter map is
checked with the old prerequisite, reasoning and knowledge engines (``engines.py``), and the naksha, the
compact map every later section shares (``naksha.py``), is built from it.

Outputs (``run_chapter``): ``chapter_map.json`` (the full record), ``naksha.json`` (what later sections get
slices of), ``MAP.md`` (the map for a human to read: teaching order, concepts, relations, the engine checks, the
type differences between code and AI and a pass/fail line per page), ``PAGES.md`` (every item of every page with
its teacher questions), one process record per step under ``records/``.
"""
from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, asdict
from pathlib import Path

from . import cards
from . import content_types as ct
from . import engines
from . import naksha as naksha_module
from .common import SEVERITY, S, arr, checklist_text, fmt, obj, review_problems
from .runner import NOTES_SCHEMA, SectionRunner, Step

SECTION = "understand"
CONNECT = "connect"
PAGE_VERSION = "understand-page/2"
CONNECT_VERSION = "understand-connect/2"
PAGE_SCHEMA_ID = "bie.brain.understand-page/2"
CONNECT_SCHEMA_ID = "bie.brain.chapter-connect/2"
DEFAULT_OUTPUT_TOKENS = 32000

KINDS = ["heading", "paragraph", "definition", "list_point", "example", "table", "table_row", "diagram",
         "diagram_label", "equation", "symbol", "box_note", "caption", "question", "answer_option", "other"]
CONTENT_TYPES = list(ct.load().ids) + [ct.NONE]
# The Section 1 types of 21 October 2026; runs made before Task 045 are converted with content_types.json's legacy map.
LEGACY_CONTENT_TYPES = ["definition", "fact", "process", "structure", "comparison", "classification", "timeline",
                        "cause_effect", "formula", "data", "example", "question", "other"]
ASKS = ["what", "about", "where", "how", "when", "who", "whom", "which", "why", "compare", "difference",
        "evidence", "exception", "consequence"]
RELATIONS = ["part_of", "type_of", "depends_on", "causes", "contrasts_with", "compares_with", "example_of",
             "sequence_next", "located_in", "function_of", "tested_by"]


@dataclass(frozen=True)
class Course:
    title: str
    subject: str
    learners: str
    exam: str
    language: str


_obj, _arr, S = obj, arr, S
QA_SCHEMA = _obj({
    "depth": {"type": "integer", "description": "1 for a first question; 2, 3 ... for a deeper why/how on an earlier answer"},
    "ask": {"type": "string", "enum": ASKS},
    "question": S,
    "answer": S,
    "basis": {"type": "string", "enum": ["book", "outside"]},
})
ITEM_SCHEMA = _obj({
    "item_id": S,
    "kind": {"type": "string", "enum": KINDS},
    "parent_item_id": S,
    "source": {"type": "string", "enum": ["text", "image", "both"]},
    "block_ids": _arr(S),
    "where_on_page": S,
    "content": S,
    "content_type": {"type": "string", "enum": CONTENT_TYPES},
    "type_note": S,
    "teachable": {"type": "boolean"},
    "teacher_understanding": _arr(QA_SCHEMA),
    "prerequisites": _arr(S),
    "exam_importance": {"type": "string", "enum": ["high", "medium", "low"]},
    "exam_note": S,
    "tests_item_ids": _arr(S),
})
PAGE_SCHEMA = _obj({
    "notes": NOTES_SCHEMA,
    "page_summary": S,
    "items": _arr(ITEM_SCHEMA),
    "boilerplate_block_ids": _arr(S),
    "text_image_disagreements": _arr(_obj({"block_ids": _arr(S), "text_says": S, "image_shows": S})),
})
PAGE_REVIEW_SCHEMA = _obj({
    "notes": NOTES_SCHEMA,
    "verdict": {"type": "string", "enum": ["pass", "fail"]},
    "missing": _arr(_obj({"what": S, "where_on_page": S, "severity": SEVERITY})),
    "wrong": _arr(_obj({"item_id": S, "problem": S, "fix": S, "severity": SEVERITY})),
    "shallow": _arr(_obj({"item_id": S, "what_is_missing": S, "severity": SEVERITY})),
    "checklist": _arr(_obj({"rule_id": S, "met": {"type": "boolean"}, "note": S})),
})
CONNECT_SCHEMA = _obj({
    "notes": NOTES_SCHEMA,
    "chapter_title": S,
    "chapter_summary": S,
    "concepts": _arr(_obj({"concept_id": S, "name": S, "item_ids": _arr(S),
                           "content_type": {"type": "string", "enum": CONTENT_TYPES}, "core_explanation": S})),
    "relations": _arr(_obj({"from_concept": S, "relation": {"type": "string", "enum": RELATIONS}, "to_concept": S, "note": S})),
    "prerequisites_to_teach": _arr(_obj({"name": S, "why_needed": S, "needed_for": _arr(S),
                                         "basis": {"type": "string", "enum": ["book", "outside"]}})),
    "cross_references": _arr(_obj({"from_item_id": S, "reference_text": S, "resolved_item_id": S})),
    "question_links": _arr(_obj({"question_item_id": S, "tests_concepts": _arr(S)})),
    "teaching_order": _arr(S),
    "exam_focus": _arr(_obj({"concept_id": S, "why": S})),
})
CONNECT_REVIEW_SCHEMA = _obj({
    "notes": NOTES_SCHEMA,
    "verdict": {"type": "string", "enum": ["pass", "fail"]},
    "problems": _arr(_obj({"where": S, "problem": S, "fix": S, "severity": SEVERITY})),
    "checklist": _arr(_obj({"rule_id": S, "met": {"type": "boolean"}, "note": S})),
})
PAGE_PATCH_SCHEMA = _obj({
    "notes": NOTES_SCHEMA,
    "replace_items": _arr(ITEM_SCHEMA),
    "remove_item_ids": _arr(S),
    "boilerplate_block_ids": _arr(S),
    "text_image_disagreements": _arr(_obj({"block_ids": _arr(S), "text_says": S, "image_shows": S})),
})


def apply_page_patch(previous: dict, patch: dict) -> dict:
    """The previous page understanding with the patch applied: items replaced or added by id, removed by id."""
    replace = {i["item_id"]: i for i in patch.get("replace_items") or []}
    removed = set(patch.get("remove_item_ids") or [])
    items = []
    for item in previous.get("items") or []:
        if item["item_id"] in removed:
            continue
        items.append(replace.pop(item["item_id"], item))
    items.extend(i for i in (patch.get("replace_items") or []) if i["item_id"] in replace)
    return dict(previous, notes=patch.get("notes") or previous.get("notes"), items=items,
                boilerplate_block_ids=patch.get("boilerplate_block_ids") or previous.get("boilerplate_block_ids") or [],
                text_image_disagreements=patch.get("text_image_disagreements") or previous.get("text_image_disagreements") or [])


# ---------------------------------------------------------------- prompts (fixed prefix texts; nothing per page)

PAGE_ROLE = """You are BIE's book-understanding section: an expert teacher of {subject} for {learners} preparing for {exam}.
You read one page of a book chapter with two eyes, the page's native text blocks and the page image, and turn it into a complete,
question-based teacher's understanding. Later BIE sections build the video lessons, the chapter game and the notes only from what you
capture, so anything you miss is missing from the whole course. Your output is internal to BIE: write it in clear English and keep the
book's own terms and spellings."""

PAGE_HOW = """For a read_page card:
- card.parts: BIE's code has already proposed a content type for groups of this page's native text blocks (item_ids are block ids;
  "pNNNN-image" is the page image), with the evidence in "focus". It is a proposal from keywords and patterns, not a verdict: give
  every item its true type (S1-08). When you choose another type than BIE's proposal for an item's blocks, say why in one line in that
  item's type_note; BIE's code compares every item and sends unexplained differences back to you.
- card.coverage: every id in must_cover must be in some item's block_ids or in boilerplate_block_ids; may_skip lists blocks BIE thinks are
  running headers or page numbers. Never list an id that is not on this page.
- card.context.before and after: one line from the previous and the next page, for context only.
How to fill the JSON:
- notes: brief notes for the reviewer: what the page is about and how it fits the chapter, the key questions a teacher must answer,
  your main decisions (how you split items, how you read an unclear part, a type you chose against BIE's proposal) with a reason each,
  and what is uncertain.
- items: everything on the page, in reading order.
  - item_id: short and unique on this page ("i1", "i2", ...).
  - kind: heading, paragraph, definition, list_point, example, table (the whole table), table_row (one per row), diagram (the whole figure),
    diagram_label (one per label), equation, symbol, box_note, caption, question (a PYQ or practice question), answer_option, other.
  - parent_item_id: the table of a table_row, the diagram of a diagram_label, the question of an answer_option, else "". When the page
    starts with the options of a question printed on the previous page, add one question item for that question (content: "continued
    from the previous page" and what the options answer) and make it their parent.
  - source: "text" if the item comes from native text blocks, "image" if it is visible only in the image, "both" if both show it.
  - block_ids: the ids of the native text blocks this item covers ([] for image-only items). Use only ids from the card.
  - where_on_page: where it is ("top table, row 2", "right diagram, label at the axon end").
  - content: the exact words for text items; a complete, faithful reading for image items (every cell with its column header for a
    table_row; what a label names and what it points to for a diagram_label; all branches for a tree).
  - content_type: one of BIE's nine type ids above, by what the content is. An example takes the type of what it illustrates; a table
    row or a diagram label usually takes its table's or diagram's type. "none" only for a question, an answer option or an item that is
    not teachable.
  - type_note: "" when you agree with BIE's proposal for this item's blocks (or there is none); otherwise one line on why your type fits.
  - teachable: false only for pure headings and containers whose children carry the content.
  - teacher_understanding: the teacher's questions and answers for this item (S1-06); depth 1 for first questions, 2 and more for
    "why"/"how" on an earlier answer; basis "book" only if the page states it, else "outside". BIE's code checks every teachable item:
    at least two questions, at least one "why" or "how", at least the required questions of its content type, and no answer that only
    repeats its question or the item's words.
  - prerequisites: concrete concepts a student must understand first.
  - exam_importance and exam_note: for this exam.
  - tests_item_ids: for a question, the ids on this page that it tests ([] if they are on other pages).
- boilerplate_block_ids: ids of running headers, page numbers, adverts, contact lines and watermarks only.
- text_image_disagreements: where the text layer and the image differ.
Reply with the JSON object only."""

PAGE_REVIEW_ROLE = """You are BIE's independent reviewer for the book-understanding section. Another AI read one page of a book and produced items
with a teacher's questions and answers on the task card you see. You get the same card, the same native text and the same page image,
and you check its work."""

PAGE_REVIEW_HOW = """You also get the maker's notes (what the page is about, its decisions with reasons, what is uncertain) and its type_note
wherever it chose another content type than BIE's code proposed.
Report concretely, each finding with a severity ("blocking" or "minor", see R-01):
- missing: anything visible on the page that no item captures (a table row, a cell, a diagram label, an arrow, a branch of a tree, a
  sentence, an equation), with where it is on the page;
- wrong: an item whose reading, kind, content type, basis or answer is wrong at this learners' level, with the fix;
- shallow: a teachable item whose questions and answers do not reach the understanding these learners need, with what is missing.
Judge at the level of a standard textbook for these learners and their exam; precision beyond that level is minor.
verdict is "pass" when nothing is blocking. Fill your own brief notes first.
Reply with the JSON object only."""

CONNECT_ROLE = """You are BIE's book-understanding section, connecting a whole chapter. You are an expert teacher of {subject} for {learners}
preparing for {exam}. The pages have already been read into items (given after the card, one line per item with its id); now build the
chapter map that the lesson, director, game and notes sections will use. Write the map in clear English with the book's terms."""

CONNECT_HOW = """For a build_chapter_map card:
- card.parts group the chapter's items by content type; card.coverage.must_cover lists every teachable item: each must be in the item_ids
  of at least one concept.
- The source lines are "item id | page | kind | type | teachable | exam | content | prerequisites".
How to fill the JSON:
- concepts: group the items into the chapter's concepts; every teachable item belongs to at least one concept (use the item ids exactly
  as given); content_type is the concept's main type (one of BIE's nine ids, never "none": a concept of practice or PYQ questions takes
  the type of what its questions test); core_explanation says the concept's heart in two or three sentences a teacher would say.
- relations: how concepts relate, using concept ids. "A depends_on B" means B must be understood first; "A causes B"; "A sequence_next B"
  means A comes before B in time or in a process. BIE's code checks with its prerequisite and reasoning engines: prerequisites never go
  in a circle, the teaching order teaches a prerequisite before what needs it, cause and effect never go in a circle, and dated concepts
  never go back in time.
- prerequisites_to_teach: what the student must understand before this chapter (or before a concept), why, and for which concept ids.
- cross_references: every reference such as "Fig. 6.10" or "see table" resolved to the item it means.
- question_links: every question item (a question "continued from the previous page" too) linked to the concepts it tests; link the
  question item, never its answer options.
- teaching_order: every concept id exactly once, in the order a teacher should teach them, starting from what the student knows.
- exam_focus: the concepts most important for this exam and why.
Reply with the JSON object only."""

CONNECT_REVIEW_ROLE = """You are BIE's independent reviewer for the chapter map of a chapter. You get the card, the chapter's items and the map
another AI made from them."""

CONNECT_REVIEW_HOW = """You also get the maker's notes. Report every problem with where it is, the fix and a severity ("blocking" or "minor",
see R-01): an item left out of all concepts, a wrong or missing relation, a prerequisite that is vague or missing, an unresolved
reference, a question not linked, a teaching order that would confuse a student, a fact wrong at this learners' level. Precision beyond
the level of a standard textbook for these learners is minor.
verdict is "pass" when nothing is blocking. Fill your own brief notes first. Reply with the JSON object only."""


PAGE_PATCH_HINT = ("Reply with a patch, not the whole page: replace_items = the complete corrected or new items (use the same item_id to "
                   "replace an item, a new item_id to add one), remove_item_ids = items to delete, and the full boilerplate_block_ids "
                   "and text_image_disagreements lists.")


def _blocks_text(page):
    if not page.blocks:
        return "(this page has no native text blocks)"
    return "\n".join(f"{b.id} | {b.text}" for b in page.blocks)


def chapter_id(course) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (course.title or "chapter").lower()).strip("-")[:40] or "chapter"


PAGE_NUMBER = re.compile(r"^\s*\d{1,4}\s*$")


def likely_boilerplate(page, neighbours) -> dict:
    """{block id: reason} for blocks BIE's code thinks are page numbers or running headers (the maker decides)."""
    out = {}
    heads = {n.blocks[0].text.strip() for n in neighbours if n is not None and n.blocks}
    for index, block in enumerate(page.blocks):
        if PAGE_NUMBER.match(block.text):
            out[block.id] = "page number"
        elif index == 0 and block.text.strip() in heads:
            out[block.id] = "running header (the same first line as the next or previous page)"
    return out


def _one_line(page, *, head: bool, header: str = "") -> str:
    if page is None:
        return ""
    lines = [b.text.strip() for b in page.blocks
             if b.text.strip() and not PAGE_NUMBER.match(b.text) and b.text.strip() != header]
    if not lines:
        return "(read from the image)"
    return naksha_module.short(lines[0] if head else lines[-1], 160)


def page_parts(page, proposals, skip, types) -> list:
    """Card parts for a page: consecutive content blocks with the same proposed type form one part."""
    image_id = f"p{page.number:04d}-image"
    content = [b for b in page.blocks if b.id not in skip]
    parts, current = [], None
    for block in content:
        proposal = proposals.get(block.id) or ct.SILENT
        kind = proposal.type or ct.NONE
        key = (kind, proposal.strength)
        if current is None or current["key"] != key:
            current = {"key": key, "ids": [], "evidence": list(proposal.evidence[:2])}
            parts.append(current)
        current["ids"].append(block.id)
    out = []
    for entry in parts:
        kind, strength = entry["key"]
        if kind != ct.NONE:     # blocks without a proposal are in must_cover; the maker decides their type
            focus = f"BIE proposes {kind} ({strength}): " + "; ".join(entry["evidence"])
            out.append(cards.part(f"b{len(out) + 1}", entry["ids"], kind, focus, types=types))
    if page.image is not None and not content:
        out.append(cards.part("img", [image_id], "figure", "This page has no native text to teach from: it is read from the image; "
                              "BIE proposes figure for its drawings, tables and labels.", types=types))
    elif page.image is not None:
        out.append(cards.part("img", [image_id], ct.NONE, "The page image: capture every table, diagram, label and arrow it shows "
                              "(S1-01); its items get the type of what they show.", types=types))
    if not out and content:
        out.append(cards.part("text", [b.id for b in content], ct.NONE, "BIE's code has no type proposal for this page's blocks: "
                              "decide each item's type yourself.", types=types))
    if not out:
        out.append(cards.part("p", [image_id], ct.NONE, "Nothing to read on this page except boilerplate.", types=types))
    return out


# ---------------------------------------------------------------- code checks

NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")


def _numbers(text: str) -> set:
    return {n.replace(",", "") for n in NUMBER.findall(text or "")}


def type_problems(rows) -> list:
    """The type differences that go back to the maker: a strong code proposal contradicted without a reason."""
    return [f"item {r['item_id']}: BIE's code proposes {r['code_type']} ({'; '.join(r['evidence'][:2])}) but you chose "
            f"{r['ai_type']}; use {r['code_type']}, or keep your type and give the reason in type_note (S1-08)"
            for r in rows if r["status"] == "disagree"]


def check_page(value: dict, page, *, proposals: dict | None = None, card: dict | None = None, types=None) -> list:
    """Problems BIE's code can see without understanding the content.

    With ``proposals`` (BIE's type per block) unexplained strong type differences go back to the maker; with ``card``
    the block coverage is the card's must_cover, checked both ways.
    """
    types = types or ct.load()
    problems = []
    items = value.get("items") or []
    known = set(page.block_ids)
    ids = [i["item_id"] for i in items]
    by_id = {i["item_id"]: i for i in items}
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        problems.append(f"item_id {dup!r} is used more than once")
    covered = set(value.get("boilerplate_block_ids") or [])
    for bad in sorted(covered - known):
        problems.append(f"boilerplate_block_ids has {bad!r}, which is not a block of this page")
    for item in items:
        iid = item["item_id"]
        unknown = [b for b in item.get("block_ids") or [] if b not in known]
        if unknown:
            problems.append(f"item {iid}: block_ids {unknown} are not blocks of this page")
        covered.update(b for b in item.get("block_ids") or [] if b in known)
        if item["source"] == "text" and not item.get("block_ids"):
            problems.append(f"item {iid}: source is 'text' but it has no block_ids")
        parent = item.get("parent_item_id") or ""
        if parent and parent not in by_id:
            problems.append(f"item {iid}: parent_item_id {parent!r} does not exist on this page")
        if item["kind"] == "table_row" and by_id.get(parent, {}).get("kind") != "table":
            problems.append(f"item {iid}: a table_row needs its table as parent_item_id")
        if item["kind"] == "diagram_label" and by_id.get(parent, {}).get("kind") != "diagram":
            problems.append(f"item {iid}: a diagram_label needs its diagram as parent_item_id")
        if item["kind"] == "answer_option" and by_id.get(parent, {}).get("kind") != "question":
            problems.append(f"item {iid}: an answer_option needs its question as parent_item_id")
        if not item.get("content", "").strip():
            problems.append(f"item {iid}: content is empty")
        for test in item.get("tests_item_ids") or []:
            if test not in by_id:
                problems.append(f"item {iid}: tests_item_ids has {test!r}, which is not an item on this page")
        kind = item.get("content_type")
        if item.get("teachable") and kind == ct.NONE and item["kind"] not in ct.ROLE_KINDS:
            problems.append(f"item {iid}: a teachable item needs one of BIE's nine content types, not 'none' (S1-08)")
        if item.get("teachable"):
            qa = item.get("teacher_understanding") or []
            asks = {q["ask"] for q in qa}
            if len(qa) < 2:
                problems.append(f"item {iid}: a teachable item needs at least two teacher questions and answers (S1-06)")
            if not asks & {"why", "how"}:
                problems.append(f"item {iid}: ask at least one 'why' or 'how' (S1-06)")
            missing_asks = [a for a in types.required_asks(kind) if a not in asks]
            if missing_asks:
                problems.append(f"item {iid}: a {kind} item must answer the required questions {missing_asks} "
                                f"({', '.join(types.word(a) for a in missing_asks)}) (S1-06, content type {kind})")
            if kind == "facts_numbers" and item["source"] == "text":
                book = set().union(*[_numbers(b.text) for b in page.blocks if b.id in set(item.get("block_ids") or [])] or [set()])
                foreign = sorted(_numbers(item.get("content", "")) - book)
                if foreign:
                    problems.append(f"item {iid}: the numbers {foreign} are not in its blocks; a fact's value must match the book "
                                    "exactly (facts_numbers check)")
            for q in qa:
                if q["answer"].strip().lower() in ("", q["question"].strip().lower(), item["content"].strip().lower()):
                    problems.append(f"item {iid}: the answer to {q['question']!r} only repeats the question or the item")
    for table in (i for i in items if i["kind"] == "table"):
        if not any(i.get("parent_item_id") == table["item_id"] and i["kind"] == "table_row" for i in items):
            problems.append(f"item {table['item_id']}: a table needs one table_row item per row (S1-03)")
    if card is not None:
        claimed = [b for i in items for b in i.get("block_ids") or []] + list(value.get("boilerplate_block_ids") or [])
        problems += cards.coverage_problems(card, [b for b in claimed if b in known], known=known, rule="S1-02")
    else:
        missing = [b for b in page.blocks if b.id not in covered]
        if missing:
            listed = "; ".join(f"{b.id} ({b.text[:50]!r})" for b in missing[:20])
            problems.append(f"{len(missing)} native text blocks are in no item and not boilerplate (S1-02): {listed}")
    boilerplate = set(value.get("boilerplate_block_ids") or [])
    if len(page.blocks) > 5 and len(boilerplate & known) > 0.6 * len(page.blocks):
        problems.append("more than 60% of the page's blocks are marked boilerplate; only headers, page numbers and adverts are (S1-02)")
    content_blocks = [b for b in page.blocks if b.id not in boilerplate]
    if page.image is not None and not content_blocks:
        from_image = [i for i in items if i["source"] in ("image", "both")]
        if len(from_image) < 3:
            problems.append("this page's text layer has no content, so it must be read from the image; "
                            "capture every table, diagram, label and branch as items (S1-01)")
    if proposals is not None:
        problems += type_problems(ct.compare(items, proposals))
    return problems


def check_connect(value: dict, items: dict) -> list:
    problems = []
    concept_ids = [c["concept_id"] for c in value.get("concepts") or []]
    known_concepts = set(concept_ids)
    for dup in sorted({c for c in concept_ids if concept_ids.count(c) > 1}):
        problems.append(f"concept_id {dup!r} is used more than once")
    grouped = set()
    for concept in value.get("concepts") or []:
        for iid in concept.get("item_ids") or []:
            if iid not in items:
                problems.append(f"concept {concept['concept_id']}: item {iid!r} does not exist")
            grouped.add(iid)
    loose = [iid for iid, item in items.items() if item.get("teachable") and iid not in grouped]
    if loose:
        problems.append(f"{len(loose)} teachable items belong to no concept: {', '.join(loose[:30])}")
    for rel in value.get("relations") or []:
        for end in (rel["from_concept"], rel["to_concept"]):
            if end not in known_concepts:
                problems.append(f"relation uses unknown concept {end!r}")
    for pre in value.get("prerequisites_to_teach") or []:
        for cid in pre.get("needed_for") or []:
            if cid not in known_concepts:
                problems.append(f"prerequisite {pre['name']!r}: needed_for has unknown concept {cid!r}")
    for ref in value.get("cross_references") or []:
        for iid in (ref["from_item_id"], ref["resolved_item_id"]):
            if iid not in items:
                problems.append(f"cross reference {ref['reference_text']!r}: item {iid!r} does not exist")
    questions = {iid for iid, item in items.items() if item["kind"] == "question"}
    linked = set()
    for link in value.get("question_links") or []:
        if link["question_item_id"] not in questions:
            problems.append(f"question_links: {link['question_item_id']!r} is not a question item")
        linked.add(link["question_item_id"])
        for cid in link.get("tests_concepts") or []:
            if cid not in known_concepts:
                problems.append(f"question {link['question_item_id']}: unknown concept {cid!r}")
    for iid in sorted(questions - linked):
        problems.append(f"question {iid} is not linked to the concepts it tests")
    order = value.get("teaching_order") or []
    if sorted(order) != sorted(known_concepts):
        extra, absent = set(order) - known_concepts, known_concepts - set(order)
        problems.append("teaching_order must list every concept id exactly once"
                        + (f"; unknown: {sorted(extra)[:10]}" if extra else "") + (f"; missing: {sorted(absent)[:10]}" if absent else ""))
    for focus in value.get("exam_focus") or []:
        if focus["concept_id"] not in known_concepts:
            problems.append(f"exam_focus uses unknown concept {focus['concept_id']!r}")
    for concept in value.get("concepts") or []:
        if concept.get("content_type") == ct.NONE:
            problems.append(f"concept {concept['concept_id']}: give it its main content type, not 'none'")
    return problems


# ---------------------------------------------------------------- steps

def page_prefixes(course, rulebook, types=None):
    """(maker prefix, reviewer prefix) of read_page: the same bytes for every page of the run."""
    types = types or ct.load()
    maker = cards.build_prefix(section=SECTION, task="read_page", version=2, schema_id=PAGE_SCHEMA_ID, schema=PAGE_SCHEMA,
                               role=fmt(PAGE_ROLE, course), how=PAGE_HOW, rulebook=rulebook, course=course, types=types)
    reviewer = cards.build_prefix(section=SECTION, task="read_page", version=2, schema_id="bie.brain.understand-page-review/2",
                                  schema=PAGE_REVIEW_SCHEMA, role=PAGE_REVIEW_ROLE, how=PAGE_REVIEW_HOW, rulebook=rulebook,
                                  course=course, types=types, review=True, checklist=checklist_text(rulebook, SECTION))
    return maker, reviewer


def page_card(course, page, *, page_count, previous=None, following=None, rulebook, prefix, proposals, skip,
              max_output_tokens=DEFAULT_OUTPUT_TOKENS, types=None) -> dict:
    types = types or ct.load()
    image_id = f"p{page.number:04d}-image"
    known = set(page.block_ids) | {image_id}
    card = cards.make(
        prefix=prefix, chapter_id=chapter_id(course),
        unit={"unit_id": f"page-{page.number:03d}", "title": f"Page {page.number} of {page_count}", "pages": [page.number]},
        parts=page_parts(page, proposals, skip, types), rules=sorted(r.id for r in rulebook.for_section(SECTION)),
        mode="full", max_output_tokens=max_output_tokens,
        must_cover=[b.id for b in page.blocks if b.id not in skip], claim_field="items[].block_ids or boilerplate_block_ids",
        may_skip=[{"item_id": b, "reason": why} for b, why in skip.items()], map_slice=[],
        before=_one_line(previous, head=False, header=page.blocks[0].text.strip() if page.blocks else ""),
        after=_one_line(following, head=True, header=page.blocks[0].text.strip() if page.blocks else ""),
        block_ids=list(page.block_ids),
        page_images=[{"page": page.number, "sha256": page.image_sha256()}] if page.image is not None else [])
    return cards.require_valid(card, prefix=prefix, rulebook=rulebook, known_ids=known, types=types)


def page_step(course: Course, page, *, page_count: int, previous=None, following=None, rulebook, max_rounds=3,
              max_output_tokens=DEFAULT_OUTPUT_TOKENS, prefixes=None) -> Step:
    types = ct.load()
    prefix, review_prefix = prefixes or page_prefixes(course, rulebook, types)
    proposals = ct.propose_blocks(page.blocks, types)
    skip = likely_boilerplate(page, (previous, following))
    card = page_card(course, page, page_count=page_count, previous=previous, following=following, rulebook=rulebook,
                     prefix=prefix, proposals=proposals, skip=skip, max_output_tokens=max_output_tokens, types=types)
    source = f"Native text blocks of this page (id | text):\n{_blocks_text(page)}"
    image = [("The page image:", page.image_part())]
    user = cards.user_message(card, source, image, "Read this page with both eyes and answer the card with the page understanding JSON.")

    def review_user(value):
        shown = {k: value[k] for k in ("notes", "page_summary", "items", "boilerplate_block_ids", "text_image_disagreements")}
        return cards.user_message(card, source + "\n\nThe understanding to review (JSON):\n" + json.dumps(shown, ensure_ascii=False),
                                  image, "Review the understanding against the page and the card; reply with the review JSON.")

    def observe(value):
        rows = ct.compare(value.get("items") or [], proposals)
        return {"type_check": rows, "type_summary": ct.summary(rows)}

    return Step(section=SECTION, unit=f"page-{page.number:03d}", instructions_version=PAGE_VERSION, system=prefix.text, user=user,
                schema=PAGE_SCHEMA, check=lambda value: check_page(value, page, proposals=proposals, card=card, types=types),
                review_system=review_prefix.text, review_user=review_user, review_schema=PAGE_REVIEW_SCHEMA,
                review_problems=review_problems, patch_schema=PAGE_PATCH_SCHEMA, apply_patch=apply_page_patch,
                patch_hint=PAGE_PATCH_HINT, max_rounds=max_rounds, card=card, observe=observe)


def _item_line(item) -> str:
    prerequisites = "; ".join(item.get("prerequisites") or [])
    content = re.sub(r"\s+", " ", item.get("content", "")).strip()
    return (f"{item['item_id']} | {item['page']} | {item['kind']} | {item['content_type']} | "
            f"{'teach' if item.get('teachable') else 'no'} | {item.get('exam_importance', '')} | {content}"
            + (f" | prerequisites: {prerequisites}" if prerequisites else ""))


def connect_step(course: Course, items: dict, *, rulebook, max_rounds=3, max_output_tokens=DEFAULT_OUTPUT_TOKENS) -> Step:
    types = ct.load()
    prefix = cards.build_prefix(section=CONNECT, task="build_chapter_map", version=2, schema_id=CONNECT_SCHEMA_ID,
                                schema=CONNECT_SCHEMA, role=fmt(CONNECT_ROLE, course), how=CONNECT_HOW, rulebook=rulebook,
                                course=course, types=types)
    review_prefix = cards.build_prefix(section=CONNECT, task="build_chapter_map", version=2,
                                       schema_id="bie.brain.chapter-connect-review/2", schema=CONNECT_REVIEW_SCHEMA,
                                       role=CONNECT_REVIEW_ROLE, how=CONNECT_REVIEW_HOW, rulebook=rulebook, course=course,
                                       types=types, review=True, checklist=checklist_text(rulebook, CONNECT))
    teachable = [iid for iid, item in items.items() if item.get("teachable")]
    by_type = {}
    for iid in teachable:
        by_type.setdefault(items[iid].get("content_type") or ct.NONE, []).append(iid)
    parts = [cards.part(f"t{n}", ids, kind, f"the {kind} items: group them into concepts and link them", types=types)
             for n, (kind, ids) in enumerate(sorted(by_type.items(), key=lambda kv: (kv[0] == ct.NONE, kv[0])), 1)]
    pages = sorted({item["page"] for item in items.values()})
    card = cards.make(
        prefix=prefix, chapter_id=chapter_id(course), unit={"unit_id": "chapter", "title": course.title, "pages": pages},
        parts=parts or [cards.part("t1", list(items)[:1], ct.NONE, "no teachable items", types=types)],
        rules=sorted(r.id for r in rulebook.for_section(CONNECT)), mode="full", max_output_tokens=max_output_tokens,
        must_cover=teachable, claim_field="concepts[].item_ids",
        may_skip=[{"item_id": iid, "reason": "not teachable (heading or container)"} for iid, item in items.items()
                  if not item.get("teachable")],
        map_slice=[], before="", after="", block_ids=[], page_images=[])
    cards.require_valid(card, prefix=prefix, rulebook=rulebook, known_ids=set(items), types=types)
    listing = "\n".join(_item_line(item) for item in items.values())
    source = f"Items of the chapter (item id | page | kind | type | teachable | exam | content | prerequisites):\n{listing}"
    user = cards.user_message(card, source, (), "Answer the card with the chapter map JSON.")

    def review_user(value):
        return cards.user_message(card, source + "\n\nThe chapter map to review (JSON):\n" + json.dumps(value, ensure_ascii=False),
                                  (), "Review the chapter map; reply with the review JSON.")

    def check(value):
        # check_connect is the card's must_cover check both ways (every teachable item in a concept, no unknown id).
        return check_connect(value, items) + engines.map_checks(value, items)[0]

    return Step(section=CONNECT, unit="chapter", instructions_version=CONNECT_VERSION, system=prefix.text, user=user,
                schema=CONNECT_SCHEMA, check=check, review_system=review_prefix.text, review_user=review_user,
                review_schema=CONNECT_REVIEW_SCHEMA, review_problems=review_problems, max_rounds=max_rounds, card=card,
                observe=lambda value: engines.map_checks(value, items)[1])


# ---------------------------------------------------------------- chapter

def _chapter_items(results):
    """All page items with chapter-wide ids ("p007-i3"); references inside a page are rewritten too."""
    items = {}
    for page_number, result in results:
        if not result.output:
            continue
        prefix = f"p{page_number:03d}-"
        local = {i["item_id"] for i in result.output.get("items") or []}

        def ref(value, prefix=prefix, local=local):
            return prefix + value if value in local else value

        for item in result.output.get("items") or []:
            entry = dict(item, page=page_number, item_id=prefix + item["item_id"],
                         parent_item_id=ref(item["parent_item_id"]) if item.get("parent_item_id") else "",
                         tests_item_ids=[ref(t) for t in item.get("tests_item_ids") or []])
            items[entry["item_id"]] = entry
    return items


def passed_pages(previous_chapter: dict) -> dict:
    """Page outputs that passed in an earlier run of the same source, to reuse instead of paying for them again.

    Items from a run before Task 045 carry the old content types; they are converted with the legacy map
    (an example takes its concept's type). Whether a page may really be reused is decided in ``run_chapter``:
    it must still pass today's code checks.
    """
    types = ct.load()
    concept_type = {}
    for concept in (previous_chapter.get("map") or {}).get("concepts") or []:
        for iid in concept.get("item_ids") or []:
            concept_type.setdefault(iid, concept.get("content_type"))
    reused = {}
    for page in previous_chapter.get("pages") or []:
        if page.get("status") != "passed":
            continue
        prefix = f"p{page['page']:03d}-"
        items = []
        for iid in page["item_ids"]:
            item = dict(previous_chapter["items"][iid])
            item.pop("page", None)
            local = lambda value: value[len(prefix):] if isinstance(value, str) and value.startswith(prefix) else value
            item.update(item_id=local(item["item_id"]), parent_item_id=local(item.get("parent_item_id") or ""),
                        tests_item_ids=[local(t) for t in item.get("tests_item_ids") or []],
                        content_type=naksha_module.item_type(item, concept_type.get(iid), types))
            item.setdefault("type_note", "")
            items.append(item)
        reused[page["page"]] = {"notes": None, "page_summary": page.get("summary", ""), "items": items,
                                "boilerplate_block_ids": page.get("boilerplate_block_ids", []),
                                "text_image_disagreements": page.get("text_image_disagreements", [])}
    return reused


def run_chapter(pdf_bytes: bytes, course: Course, runner: SectionRunner, out_dir, *, pages: str | None = None,
                workers: int = 4, max_rounds: int = 3, with_images: bool = True, previous_chapter: dict | None = None,
                max_output_tokens: int = DEFAULT_OUTPUT_TOKENS):
    from .pages import load_pages
    from .runner import StepResult

    types = ct.load()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    source_sha, page_count, page_list = load_pages(pdf_bytes, pages, with_images=with_images)
    offered = {}
    if previous_chapter and previous_chapter.get("source_sha256") == source_sha:
        offered = passed_pages(previous_chapter)
    prefixes = page_prefixes(course, runner.rulebook, types)
    reuse, rechecked, steps = {}, {}, []
    for index, page in enumerate(page_list):
        previous = page_list[index - 1] if index > 0 else None
        following = page_list[index + 1] if index + 1 < len(page_list) else None
        if page.number in offered:
            # Reuse only what still passes today's code checks (types, required questions, coverage).
            proposals = ct.propose_blocks(page.blocks, types)
            problems = check_page(offered[page.number], page, proposals=proposals, types=types)
            rechecked[page.number] = problems
            if not problems:
                reuse[page.number] = offered[page.number]
                continue
        steps.append((page.number, page_step(course, page, page_count=page_count, previous=previous, following=following,
                                             rulebook=runner.rulebook, max_rounds=max_rounds,
                                             max_output_tokens=max_output_tokens, prefixes=prefixes)))
    book = cards.CardBook()                 # a card id is used once per run
    for _, step in steps:
        book.add(step.card)
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        fresh = dict(zip([n for n, _ in steps], pool.map(lambda pair: runner.run(pair[1]), steps)))
    results = []
    for page in page_list:
        if page.number in reuse:
            results.append((page.number, StepResult(SECTION, f"page-{page.number:03d}", "passed", reuse[page.number],
                                                    record_path=None)))
        else:
            results.append((page.number, fresh[page.number]))
    items = _chapter_items(results)
    connect = None
    if items:
        step = connect_step(course, items, rulebook=runner.rulebook, max_rounds=max_rounds, max_output_tokens=max_output_tokens)
        book.add(step.card)
        connect = runner.run(step)
    type_rows = []
    for number, result in results:
        page = next(pg for pg in page_list if pg.number == number)
        rows = ct.compare((result.output or {}).get("items") or [], ct.propose_blocks(page.blocks, types))
        type_rows += [dict(r, item_id=f"p{number:03d}-{r['item_id']}", page=number) for r in rows]
    chapter = {
        "schema": "bie.brain.chapter-map/2",
        "course": asdict(course),
        "source_sha256": source_sha,
        "page_count": page_count,
        "rulebook_version": runner.rulebook.version,
        "content_types_version": types.version,
        "maker_route": runner.maker,
        "reviewer_route": runner.reviewer,
        "reviewer_independence": runner.independence,
        "pages": [{
            "page": number,
            "status": result.status,
            "rounds": len(result.rounds),
            "summary": (result.output or {}).get("page_summary", ""),
            "boilerplate_block_ids": (result.output or {}).get("boilerplate_block_ids", []),
            "text_image_disagreements": (result.output or {}).get("text_image_disagreements", []),
            "item_ids": [iid for iid, item in items.items() if item["page"] == number],
            "last_problems": (result.rounds[-1].get("code_problems") or []) + (result.rounds[-1].get("review_problems") or [])
            if result.rounds and not result.passed else [],
            "record": Path(result.record_path).name if result.record_path else None,
            "reused": number in reuse,
            "reuse_refused": rechecked.get(number, [])[:10] if number in rechecked and number not in reuse else [],
            "cost_usd": result.cost_usd,
            "seconds": result.seconds,
        } for number, result in results],
        "items": items,
        "map": {k: v for k, v in (connect.output or {}).items() if k != "notes"} if connect else {},
        "map_status": connect.status if connect else "not_run",
        "map_record": Path(connect.record_path).name if connect and connect.record_path else None,
        "map_checks": (connect.rounds[-1].get("observed") if connect and connect.rounds else None) or {},
        "type_check": {"summary": ct.summary(type_rows),
                       "differences": [r for r in type_rows if r["status"] in ("disagree", "explained", "differs_weak")]},
        "cost_usd": round(sum(r.cost_usd for _, r in results) + (connect.cost_usd if connect else 0.0), 6),
        "prefixes": {prefixes[0].prefix_id: prefixes[0].sha256, prefixes[1].prefix_id: prefixes[1].sha256},
    }
    if connect and connect.output:
        built = naksha_module.build(chapter, types)
        (out / "naksha.json").write_text(json.dumps(built, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        chapter["naksha"] = dict(naksha_module.size(built), sha256=built["sha256"], status=connect.status)
    chapter["quality"] = quality(chapter)
    (out / "chapter_map.json").write_text(json.dumps(chapter, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "MAP.md").write_text(render_markdown(chapter), encoding="utf-8")
    (out / "PAGES.md").write_text(render_pages(chapter), encoding="utf-8")
    return chapter


def quality(chapter: dict) -> dict:
    items = chapter["items"].values()
    teachable = [i for i in items if i.get("teachable")]
    qa = [q for i in teachable for q in i.get("teacher_understanding") or []]
    return {
        "pages": len(chapter["pages"]),
        "pages_passed": sum(1 for p in chapter["pages"] if p["status"] == "passed"),
        "pages_reused": sum(1 for p in chapter["pages"] if p.get("reused")),
        "map_passed": chapter["map_status"] == "passed",
        "items": len(chapter["items"]),
        "teachable_items": len(teachable),
        "items_from_image": sum(1 for i in items if i["source"] in ("image", "both")),
        "teacher_questions": len(qa),
        "deeper_questions": sum(1 for q in qa if q["depth"] >= 2),
        "outside_answers": sum(1 for q in qa if q["basis"] == "outside"),
        "type_check": (chapter.get("type_check") or {}).get("summary", {}),
        "naksha_tokens_estimate": (chapter.get("naksha") or {}).get("tokens_estimate"),
        "cost_usd": chapter["cost_usd"],
        "cost_usd_per_page": round(chapter["cost_usd"] / max(1, len(chapter["pages"])), 6),
    }


def render_markdown(chapter: dict) -> str:
    q = chapter["quality"]
    course = chapter["course"]
    independence = chapter.get("reviewer_independence")
    lines = [f"# Chapter map · {course['title']}", "",
             f"{course['subject']} · {course['learners']} · {course['exam']} · learner language {course['language']}", "",
             f"Maker `{chapter['maker_route']}`, reviewer `{chapter['reviewer_route']}`"
             + (" (same company, another model: temporary, kamzor jaanch)" if independence == "same_company_temporary" else "")
             + (" (the same model in a fresh call: kamzor jaanch, the weakest check)" if independence == "same_model_temporary" else "")
             + f", rulebook `{chapter['rulebook_version']}`.", "",
             f"- Pages passed: {q['pages_passed']} of {q['pages']} ({q.get('pages_reused', 0)} reused from an earlier run); "
             f"chapter map: {chapter['map_status']}",
             f"- Items: {q['items']} ({q['teachable_items']} teachable, {q['items_from_image']} read from the image)",
             f"- Teacher questions: {q['teacher_questions']} ({q['deeper_questions']} deeper why/how, {q['outside_answers']} from outside the book)",
             f"- Estimated cost: {money(q['cost_usd'], chapter)} ({money(q['cost_usd_per_page'], chapter)} per page)"]
    if chapter.get("naksha"):
        n = chapter["naksha"]
        lines.append(f"- Naksha (the compact map later sections get slices of): {n['items']} items, {n['concepts']} concepts, "
                     f"{n['links']} links, {n['chars']:,} characters, about {n['tokens_estimate']:,} tokens")
    lines.append("")
    type_check = chapter.get("type_check") or {}
    if type_check.get("summary"):
        lines += ["## Content types: BIE's code and the AI", "",
                  "BIE's code proposes a type from keywords and patterns before the AI reads the page. "
                  + ", ".join(f"{k}: {v}" for k, v in type_check["summary"].items()) + ".", ""]
        for row in type_check.get("differences", [])[:40]:
            item = chapter["items"].get(row["item_id"], {})
            note = f" · AI's reason: {row['type_note']}" if row.get("type_note") else ""
            lines.append(f"- **{row['item_id']}** ({row['status']}): code `{row['code_type']}` ({row['strength']}), "
                         f"AI `{row['ai_type']}`{note} · {naksha_module.short(item.get('content', ''), 90)}")
        lines.append("")
    m = chapter.get("map") or {}
    if m:
        names = {c["concept_id"]: c["name"] for c in m.get("concepts", [])}
        lines += ["## Teaching order", ""] + [f"{n}. {names.get(c, c)}" for n, c in enumerate(m.get("teaching_order", []), 1)] + [""]
        lines += ["## Prerequisites to teach first", ""] + [
            f"- **{p['name']}** ({p['basis']}): {p['why_needed']}" for p in m.get("prerequisites_to_teach", [])] + [""]
        lines += ["## Concepts", ""]
        for c in m.get("concepts", []):
            lines += [f"### {c['name']} · {c['content_type']}", "", c["core_explanation"], "", "Items: " + ", ".join(c["item_ids"]), ""]
        if m.get("relations"):
            lines += ["## Relations", ""] + [f"- {names.get(r['from_concept'], r['from_concept'])} **{r['relation']}** "
                                             f"{names.get(r['to_concept'], r['to_concept'])}" + (f" · {r['note']}" if r['note'] else "")
                                             for r in m["relations"]] + [""]
        checks = chapter.get("map_checks") or {}
        if checks:
            lines += ["## Engine checks on the map (PR, RE, KI)", ""] + [f"- {k}: {json.dumps(v, ensure_ascii=False)}"
                                                                          for k, v in checks.items()] + [""]
    lines += ["## Pages", "", "| Page | Result | Rounds | Items | Cost |", "| --- | --- | --- | --- | --- |"]
    for p in chapter["pages"]:
        result = p["status"] + (" (reused)" if p.get("reused") else "")
        cost = "—" if p.get("reused") else money(p.get("cost_usd") or 0, chapter)
        lines.append(f"| {p['page']} | {result} | {p['rounds']} | {len(p['item_ids'])} | {cost} |")
    open_pages = [p for p in chapter["pages"] if p["status"] != "passed" and p["last_problems"]]
    if open_pages:
        lines += ["", "Open problems of the pages that did not pass:", ""]
        lines += [f"- Page {p['page']}: " + "; ".join(x[:160] for x in p["last_problems"][:3]) for p in open_pages]
    lines += ["", "Every item with its teacher questions: `PAGES.md`.", ""]
    return "\n".join(lines)


def money(usd: float, run: dict) -> str:
    """Rupees when the run's exchange rate is known (``run["usd_inr"]``, set by tools/render_run.py from SUMMARY.json),
    else dollars. The amount is the ledger's estimate, not the bill."""
    rate = run.get("usd_inr")
    return f"₹{usd * rate:.2f}" if rate else f"${usd:.4f}"


def render_pages(chapter: dict) -> str:
    """Every item of every page with its teacher questions (the long companion of MAP.md)."""
    lines = [f"# Pages · {chapter['course']['title']}", ""]
    for p in chapter["pages"]:
        lines += [f"## Page {p['page']} · {p['status']} after {p['rounds']} round(s)" + (" · reused" if p.get("reused") else ""),
                  "", p["summary"], ""]
        if p["last_problems"]:
            lines += ["Open problems:", ""] + [f"- {x}" for x in p["last_problems"][:15]] + [""]
        for iid in p["item_ids"]:
            item = chapter["items"][iid]
            lines.append(f"- **{iid}** · {item['kind']} · {item['content_type']} · {item['source']}"
                         + (" · exam " + item["exam_importance"] if item.get("teachable") else ""))
            lines.append(f"  - {item['content']}")
            for qa in item.get("teacher_understanding") or []:
                indent = "  " * (qa["depth"] + 1)
                tag = "" if qa["basis"] == "book" else " _(outside the book)_"
                lines.append(f"{indent}- {qa['ask']}: {qa['question']} → {qa['answer']}{tag}")
            if item.get("prerequisites"):
                lines.append("  - prerequisites: " + "; ".join(item["prerequisites"]))
        lines.append("")
    return "\n".join(lines)
