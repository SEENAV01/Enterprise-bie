"""Section 1 · Understanding the book.

Each page is read with two eyes (native text blocks and the page image) into items with page
locations, and every teachable item is understood through a teacher's questions (what, where, how,
why, compare, difference ... and deeper "why" and "how" on the answers). Then one chapter step
connects the items into concepts, relations, prerequisites to teach, resolved cross-references and
a teaching order. Every step goes through ``SectionRunner``: code checks, an independent reviewer
on another provider, bounded remakes and a full process record.

Outputs (``run_chapter``): ``chapter_map.json`` (what later sections consume), ``MAP.md`` (the same
map for a human to check), one process record per step under ``records/``.
"""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, asdict
from pathlib import Path

from .common import SEVERITY, S, arr, checklist_text, fmt, obj, review_problems
from .runner import NOTES_SCHEMA, SectionRunner, Step

SECTION = "understand"
CONNECT = "connect"
PAGE_VERSION = "understand-page/1"
CONNECT_VERSION = "understand-connect/1"

KINDS = ["heading", "paragraph", "definition", "list_point", "example", "table", "table_row", "diagram",
         "diagram_label", "equation", "symbol", "box_note", "caption", "question", "answer_option", "other"]
CONTENT_TYPES = ["definition", "fact", "process", "structure", "comparison", "classification", "timeline",
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


# ---------------------------------------------------------------- prompts

PAGE_ROLE = """You are BIE's book-understanding section: an expert teacher of {subject} for {learners} preparing for {exam}.
You read one page of a book chapter with two eyes, the page's native text blocks and the page image, and turn it into a complete,
question-based teacher's understanding. Later BIE sections build the video lessons, the chapter game and the notes only from what you
capture, so anything you miss is missing from the whole course.

Course: "{title}" · subject: {subject} · learners: {learners} · exam: {exam} · learner language: {language}.
Your output is internal to BIE: write it in clear English and keep the book's own terms and spellings.

Navin's rules for this section (follow every one):
{rules}

How to fill the JSON:
- notes: brief notes for the reviewer: what the page is about and how it fits the chapter, the key questions a teacher must answer,
  your main decisions (how you split items, how you read an unclear part) with a reason each, and what is uncertain.
- items: everything on the page, in reading order.
  - item_id: short and unique on this page ("i1", "i2", ...).
  - kind: heading, paragraph, definition, list_point, example, table (the whole table), table_row (one per row), diagram (the whole figure),
    diagram_label (one per label), equation, symbol, box_note, caption, question (a PYQ or practice question), answer_option, other.
  - parent_item_id: the table of a table_row, the diagram of a diagram_label, the question of an answer_option, else "".
  - source: "text" if the item comes from native text blocks, "image" if it is visible only in the image, "both" if both show it.
  - block_ids: the ids of the native text blocks this item covers ([] for image-only items). Use only ids from the list given.
  - where_on_page: where it is ("top table, row 2", "right diagram, label at the axon end").
  - content: the exact words for text items; a complete, faithful reading for image items (every cell with its column header for a
    table_row; what a label names and what it points to for a diagram_label; all branches for a tree).
  - content_type: what the content really is (definition, fact, process, structure, comparison, classification, timeline, cause_effect,
    formula, data, example, question, other).
  - teachable: false only for pure headings and containers whose children carry the content.
  - teacher_understanding: the teacher's questions and answers for this item (see S1-06); depth 1 for first questions, 2 and more for
    "why"/"how" on an earlier answer; basis "book" only if the page states it, else "outside". BIE's code checks every teachable item:
    at least two questions, at least one "why" or "how"; a process needs "how"; a comparison or classification needs "compare" or
    "difference".
  - prerequisites: concrete concepts a student must understand first.
  - exam_importance and exam_note: for this exam.
  - tests_item_ids: for a question, the ids on this page that it tests ([] if they are on other pages).
- boilerplate_block_ids: ids of running headers, page numbers, adverts, contact lines and watermarks only.
- text_image_disagreements: where the text layer and the image differ.
Reply with the JSON object only."""

PAGE_REVIEW_ROLE = """You are BIE's independent reviewer for the book-understanding section. Another AI read one page of a {subject} book for
{learners} ({exam}) and produced items with a teacher's questions and answers. You see the same page image and native text, and you check
its work.

{review_rules}

Check against this list (answer every item in "checklist" with its rule id):
{checklist}

You also get the maker's notes (what the page is about, its decisions with reasons, what is uncertain).

Report concretely, each finding with a severity ("blocking" or "minor", see R-01):
- missing: anything visible on the page that no item captures (a table row, a cell, a diagram label, an arrow, a branch of a tree, a
  sentence, an equation), with where it is on the page;
- wrong: an item whose reading, kind, content type, basis or answer is wrong at this learners' level, with the fix;
- shallow: a teachable item whose questions and answers do not reach the understanding these learners need, with what is missing.
Judge at the level of a standard textbook for {learners} ({exam}); precision beyond that level is minor.
verdict is "pass" when nothing is blocking. Fill your own brief notes first.
Reply with the JSON object only."""

CONNECT_ROLE = """You are BIE's book-understanding section, connecting a whole chapter. You are an expert teacher of {subject} for {learners}
preparing for {exam}. The pages have already been read into items (given below with ids); now build the chapter map that the lesson,
director, game and notes sections will use.

Course: "{title}" · learner language: {language}. Write the map in clear English with the book's terms.

Navin's rules for this step (follow every one):
{rules}

How to fill the JSON:
- concepts: group the items into the chapter's concepts; every teachable item belongs to at least one concept (use the item ids exactly
  as given); core_explanation says the concept's heart in two or three sentences a teacher would say.
- relations: how concepts relate, using concept ids.
- prerequisites_to_teach: what the student must understand before this chapter (or before a concept), why, and for which concept ids.
- cross_references: every reference such as "Fig. 6.10" or "see table" resolved to the item it means.
- question_links: every question item linked to the concepts it tests.
- teaching_order: every concept id exactly once, in the order a teacher should teach them, starting from what the student knows.
- exam_focus: the concepts most important for this exam and why.
Reply with the JSON object only."""

CONNECT_REVIEW_ROLE = """You are BIE's independent reviewer for the chapter map of a {subject} chapter ({learners}, {exam}). You get the
chapter's items and the map another AI made from them.

{review_rules}

Check against this list (answer every item in "checklist" with its rule id):
{checklist}

You also get the maker's notes. Report every problem with where it is, the fix and a severity ("blocking" or "minor", see R-01): an
item left out of all concepts, a wrong or missing relation, a prerequisite that is vague or missing, an unresolved reference, a question
not linked, a teaching order that would confuse a student, a fact wrong at this learners' level. Precision beyond the level of a standard
textbook for {learners} ({exam}) is minor.
verdict is "pass" when nothing is blocking. Fill your own brief notes first. Reply with the JSON object only."""


PAGE_PATCH_HINT = ("Reply with a patch, not the whole page: replace_items = the complete corrected or new items (use the same item_id to "
                   "replace an item, a new item_id to add one), remove_item_ids = items to delete, and the full boilerplate_block_ids "
                   "and text_image_disagreements lists.")


def _blocks_text(page):
    if not page.blocks:
        return "(this page has no native text blocks)"
    return "\n".join(f"{b.id} | {b.text}" for b in page.blocks)


def _context_lines(page, *, head: bool, count: int = 8):
    if page is None or not page.blocks:
        return "(none)"
    blocks = page.blocks[:count] if head else page.blocks[-count:]
    return "\n".join(b.text for b in blocks)


# ---------------------------------------------------------------- code checks

def check_page(value: dict, page) -> list:
    """Problems BIE's code can see without understanding the content."""
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
        if item.get("teachable"):
            qa = item.get("teacher_understanding") or []
            asks = {q["ask"] for q in qa}
            if len(qa) < 2:
                problems.append(f"item {iid}: a teachable item needs at least two teacher questions and answers (S1-06)")
            if not asks & {"why", "how"}:
                problems.append(f"item {iid}: ask at least one 'why' or 'how' (S1-06)")
            if item["content_type"] == "process" and "how" not in asks:
                problems.append(f"item {iid}: a process needs a 'how' question (S1-06)")
            if item["content_type"] in ("comparison", "classification") and not asks & {"compare", "difference"}:
                problems.append(f"item {iid}: a {item['content_type']} needs a 'compare' or 'difference' question (S1-06)")
            for q in qa:
                if q["answer"].strip().lower() in ("", q["question"].strip().lower(), item["content"].strip().lower()):
                    problems.append(f"item {iid}: the answer to {q['question']!r} only repeats the question or the item")
    for table in (i for i in items if i["kind"] == "table"):
        if not any(i.get("parent_item_id") == table["item_id"] and i["kind"] == "table_row" for i in items):
            problems.append(f"item {table['item_id']}: a table needs one table_row item per row (S1-03)")
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
    return problems


# ---------------------------------------------------------------- steps

def page_step(course: Course, page, *, page_count: int, previous=None, following=None, rulebook, max_rounds=3) -> Step:
    system = fmt(PAGE_ROLE, course, rules=rulebook.instructions(SECTION))
    intro = (f"Chapter: {course.title}. Page {page.number} of {page_count}.\n\n"
             f"Last lines of the previous page (context only):\n{_context_lines(previous, head=False)}\n\n"
             f"First lines of the next page (context only):\n{_context_lines(following, head=True)}\n\n"
             f"Native text blocks of this page (id | text):\n{_blocks_text(page)}")
    user = [{"type": "text", "text": intro}]
    if page.image_part():
        user += [{"type": "text", "text": "The page image:"}, page.image_part()]
    user.append({"type": "text", "text": "Read this page with both eyes and reply with the page understanding JSON."})
    review_system = fmt(PAGE_REVIEW_ROLE, course, review_rules=rulebook.reviewer_instructions(),
                         checklist=checklist_text(rulebook, SECTION))

    def review_user(value):
        shown = {k: value[k] for k in ("notes", "page_summary", "items", "boilerplate_block_ids", "text_image_disagreements")}
        parts = [{"type": "text", "text": f"Chapter: {course.title}. Page {page.number} of {page_count}.\n\n"
                                          f"Native text blocks (id | text):\n{_blocks_text(page)}"}]
        if page.image_part():
            parts += [{"type": "text", "text": "The page image:"}, page.image_part()]
        parts.append({"type": "text", "text": "The understanding to review (JSON):\n" + json.dumps(shown, ensure_ascii=False)})
        return parts

    return Step(section=SECTION, unit=f"page-{page.number:03d}", instructions_version=PAGE_VERSION, system=system, user=user,
                schema=PAGE_SCHEMA, check=lambda value: check_page(value, page), review_system=review_system,
                review_user=review_user, review_schema=PAGE_REVIEW_SCHEMA, review_problems=review_problems,
                patch_schema=PAGE_PATCH_SCHEMA, apply_patch=apply_page_patch, patch_hint=PAGE_PATCH_HINT, max_rounds=max_rounds)


def _compact_items(items: dict):
    rows = []
    for iid, item in items.items():
        rows.append({"id": iid, "page": item["page"], "kind": item["kind"], "type": item["content_type"],
                     "teachable": item["teachable"], "content": item["content"], "prerequisites": item.get("prerequisites", []),
                     "exam": item.get("exam_importance")})
    return rows


def connect_step(course: Course, items: dict, *, rulebook, max_rounds=3) -> Step:
    system = fmt(CONNECT_ROLE, course, rules=rulebook.instructions(CONNECT))
    listing = json.dumps(_compact_items(items), ensure_ascii=False)
    user = f"Chapter: {course.title}.\nItems of the chapter (JSON list):\n{listing}\n\nReply with the chapter map JSON."
    review_system = fmt(CONNECT_REVIEW_ROLE, course, review_rules=rulebook.reviewer_instructions(),
                         checklist=checklist_text(rulebook, CONNECT))

    def review_user(value):
        shown = value
        return (f"Chapter: {course.title}.\nItems (JSON list):\n{listing}\n\n"
                f"The chapter map to review (JSON):\n{json.dumps(shown, ensure_ascii=False)}")

    return Step(section=CONNECT, unit="chapter", instructions_version=CONNECT_VERSION, system=system, user=user,
                schema=CONNECT_SCHEMA, check=lambda value: check_connect(value, items), review_system=review_system,
                review_user=review_user, review_schema=CONNECT_REVIEW_SCHEMA, review_problems=review_problems,
                max_rounds=max_rounds)


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
    """Page outputs that passed in an earlier run of the same source, to reuse instead of paying for them again."""
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
                        tests_item_ids=[local(t) for t in item.get("tests_item_ids") or []])
            items.append(item)
        reused[page["page"]] = {"notes": None, "page_summary": page.get("summary", ""), "items": items,
                                "boilerplate_block_ids": page.get("boilerplate_block_ids", []),
                                "text_image_disagreements": page.get("text_image_disagreements", [])}
    return reused


def run_chapter(pdf_bytes: bytes, course: Course, runner: SectionRunner, out_dir, *, pages: str | None = None,
                workers: int = 4, max_rounds: int = 3, with_images: bool = True, previous_chapter: dict | None = None):
    from .pages import load_pages
    from .runner import StepResult

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    source_sha, page_count, page_list = load_pages(pdf_bytes, pages, with_images=with_images)
    reuse = {}
    if previous_chapter and previous_chapter.get("source_sha256") == source_sha:
        reuse = passed_pages(previous_chapter)
    steps = []
    for index, page in enumerate(page_list):
        if page.number in reuse:
            continue
        previous = page_list[index - 1] if index > 0 else None
        following = page_list[index + 1] if index + 1 < len(page_list) else None
        steps.append((page.number, page_step(course, page, page_count=page_count, previous=previous, following=following,
                                             rulebook=runner.rulebook, max_rounds=max_rounds)))
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
    connect = runner.run(connect_step(course, items, rulebook=runner.rulebook, max_rounds=max_rounds)) if items else None
    chapter = {
        "schema": "bie.brain.chapter-map/1",
        "course": asdict(course),
        "source_sha256": source_sha,
        "page_count": page_count,
        "rulebook_version": runner.rulebook.version,
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
            "cost_usd": result.cost_usd,
            "seconds": result.seconds,
        } for number, result in results],
        "items": items,
        "map": {k: v for k, v in (connect.output or {}).items() if k != "notes"} if connect else {},
        "map_status": connect.status if connect else "not_run",
        "map_record": Path(connect.record_path).name if connect and connect.record_path else None,
        "cost_usd": round(sum(r.cost_usd for _, r in results) + (connect.cost_usd if connect else 0.0), 6),
    }
    chapter["quality"] = quality(chapter)
    (out / "chapter_map.json").write_text(json.dumps(chapter, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "MAP.md").write_text(render_markdown(chapter), encoding="utf-8")
    return chapter


def quality(chapter: dict) -> dict:
    items = chapter["items"].values()
    teachable = [i for i in items if i.get("teachable")]
    qa = [q for i in teachable for q in i.get("teacher_understanding") or []]
    return {
        "pages": len(chapter["pages"]),
        "pages_passed": sum(1 for p in chapter["pages"] if p["status"] == "passed"),
        "map_passed": chapter["map_status"] == "passed",
        "items": len(chapter["items"]),
        "teachable_items": len(teachable),
        "items_from_image": sum(1 for i in items if i["source"] in ("image", "both")),
        "teacher_questions": len(qa),
        "deeper_questions": sum(1 for q in qa if q["depth"] >= 2),
        "outside_answers": sum(1 for q in qa if q["basis"] == "outside"),
        "cost_usd": chapter["cost_usd"],
        "cost_usd_per_page": round(chapter["cost_usd"] / max(1, len(chapter["pages"])), 6),
    }


def render_markdown(chapter: dict) -> str:
    q = chapter["quality"]
    course = chapter["course"]
    lines = [f"# Chapter map · {course['title']}", "",
             f"{course['subject']} · {course['learners']} · {course['exam']} · learner language {course['language']}", "",
             f"Maker `{chapter['maker_route']}`, reviewer `{chapter['reviewer_route']}`"
             + (" (same company, another model: temporary)" if chapter.get("reviewer_independence") == "same_company_temporary" else "")
             + f", rulebook `{chapter['rulebook_version']}`.", "",
             f"- Pages passed: {q['pages_passed']} of {q['pages']}; chapter map: {chapter['map_status']}",
             f"- Items: {q['items']} ({q['teachable_items']} teachable, {q['items_from_image']} read from the image)",
             f"- Teacher questions: {q['teacher_questions']} ({q['deeper_questions']} deeper why/how, {q['outside_answers']} from outside the book)",
             f"- Estimated cost: ${q['cost_usd']:.4f} (${q['cost_usd_per_page']:.4f} per page)", ""]
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
    lines += ["## Pages", ""]
    for p in chapter["pages"]:
        lines += [f"### Page {p['page']} · {p['status']} after {p['rounds']} round(s)", "", p["summary"], ""]
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
