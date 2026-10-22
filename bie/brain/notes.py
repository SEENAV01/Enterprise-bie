"""Section 7 · Notes: question-based summary notes as interactive infographic slides (Navin's summariser design).

For every concept of the chapter map BIE writes slides that each answer one question (what, why, how,
who/whom, when/where, evidence, reasoning, insight, difference, limitation, conclusion), in three depths
(quick essence, understand, deep dive), with the source pages of every statement, "the book does not
say" where the book is silent, PYQ links, and one infographic whose form follows the content type
(process → flow, dates → timeline, comparison → difference table, numbers → chart, cause and effect →
relationship diagram, main idea and branches → concept map or tree). Visuals are data; BIE's renderer
draws them, so no slide is a generated image.

Outputs (``run_notes``): ``notes.json`` and, from ``render_notes_html``, one self-contained interactive
HTML deck (its print view is the PDF).
"""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .common import SEVERITY, S, arr, checklist_text, fmt, obj, review_problems
from .lesson import question_ids
from .runner import NOTES_SCHEMA, Step
from .understanding import Course

SECTION = "notes"
VERSION = "notes-concept/1"
ASKS = ["what", "why", "how", "who_whom", "when_where", "evidence", "reasoning", "insight", "difference", "limitation",
        "conclusion"]
VISUALS = ["flow", "timeline", "difference_table", "chart", "relationship", "concept_map", "tree", "labelled_list", "none"]
VISUAL_SCHEMA = obj({
    "type": {"type": "string", "enum": VISUALS},
    "title": S,
    "steps": arr(obj({"label": S, "detail": S})),
    "events": arr(obj({"when": S, "label": S, "detail": S})),
    "columns": arr(S),
    "rows": arr(obj({"label": S, "cells": arr(S)})),
    "series": arr(obj({"label": S, "value": {"type": "number"}, "unit": S})),
    "nodes": arr(obj({"id": S, "label": S, "parent_id": S, "detail": S})),
    "edges": arr(obj({"from_id": S, "to_id": S, "label": S})),
})
SLIDE_SCHEMA = obj({
    "slide_id": S,
    "ask": {"type": "string", "enum": ASKS},
    "question": S,
    "essence": S,
    "answer": S,
    "deep_dive": S,
    "visual": VISUAL_SCHEMA,
    "source_item_ids": arr(S),
    "basis": {"type": "string", "enum": ["book", "outside", "mixed"]},
    "not_in_book": S,
    "pyq_item_ids": arr(S),
})
NOTES_OUT_SCHEMA = obj({"notes": NOTES_SCHEMA, "slides": arr(SLIDE_SCHEMA)})
PATCH_SCHEMA = obj({"notes": NOTES_SCHEMA, "replace_slides": arr(SLIDE_SCHEMA), "remove_slide_ids": arr(S)})
PATCH_HINT = ("Reply with a patch, not every slide: replace_slides = complete corrected or new slides (same slide_id replaces), "
              "remove_slide_ids = slides to delete.")
REVIEW_SCHEMA = obj({
    "notes": NOTES_SCHEMA,
    "verdict": {"type": "string", "enum": ["pass", "fail"]},
    "problems": arr(obj({"where": S, "problem": S, "fix": S, "severity": SEVERITY})),
    "checklist": arr(obj({"rule_id": S, "met": {"type": "boolean"}, "note": S})),
})

ROLE = """You are BIE's notes section: you turn one concept of a {subject} chapter into question-based revision notes for {learners}
({exam}), the way Navin designed them: every slide answers one question, in three depths, with an infographic whose form follows the
content. Students revise from these notes, so nothing important may be missing and nothing may be invented.

Course: "{title}" · learner language: {language} (write question, essence, answer and deep dive in {language}; keep the book's English
terms; labels inside visuals use the book's terms).

Navin's rules for this section (follow every one):
{rules}

How to fill the JSON:
- notes: brief notes for the reviewer: what the concept is about, the key questions, your main decisions with a reason each, what is
  uncertain.
- slides: in teaching order. slide_id "n1", "n2" ...; ask = the kind of question; question = the question itself; essence = the quick
  answer in one line; answer = the "understand" depth (a few short sentences); deep_dive = evidence, exceptions and what the book says
  exactly; visual = the infographic as data (type: flow uses steps; timeline uses events; difference_table uses columns and rows with
  one cell per column; chart uses series with numbers; relationship uses nodes and edges; concept_map and tree use nodes with
  parent_id; labelled_list uses nodes; leave the arrays you do not use empty); source_item_ids = the chapter-map items this slide is
  based on; basis = book, outside or mixed; not_in_book = "" or what a student might expect but the book does not say; pyq_item_ids =
  question items of the chapter that this slide answers.
Every teachable item listed for this concept must be the source of some slide. Reply with the JSON object only."""

REVIEW_ROLE = """You are BIE's independent reviewer for the notes section ({subject}, {learners}, {exam}, language {language}). Another AI
wrote question-based infographic notes for one concept from BIE's chapter map. Judge them as Navin would: can a student revise the
whole concept quickly and deeply from them, with nothing invented?

{review_rules}

Check against this list (answer every item in "checklist" with its rule id):
{checklist}

You also get the maker's notes. Report every problem with where it is (slide id), what is wrong, the fix and a severity ("blocking" or
"minor", see R-01): an item not covered, an answer that is wrong at this level or not supported by the book while marked "book", an
invented fact, a visual whose form does not match the content, a deep dive that adds nothing, a missing "the book does not say".
Precision beyond the level of a standard textbook for {learners} ({exam}) is minor.
verdict is "pass" when nothing is blocking. Fill your own brief notes first. Reply with the JSON object only."""


def _concept_input(chapter, concept):
    items = [chapter["items"][i] for i in concept["item_ids"] if i in chapter["items"]]
    rows = []
    for item in items:
        rows.append({"item_id": item["item_id"], "page": item["page"], "kind": item["kind"], "content_type": item["content_type"],
                     "teachable": item["teachable"], "content": item["content"],
                     "teacher_questions": [{"id": qid, "question": qa["question"], "answer": qa["answer"], "basis": qa["basis"]}
                                           for qid, qa in zip(question_ids(item), item.get("teacher_understanding") or [])]})
    questions = [{"item_id": i["item_id"], "content": i["content"]} for i in chapter["items"].values() if i["kind"] == "question"]
    return {"concept": {k: concept[k] for k in ("concept_id", "name", "content_type", "core_explanation")}, "items": rows,
            "chapter_questions": questions}, {i["item_id"] for i in items if i.get("teachable")}


def check_slides(value: dict, chapter: dict, teachable: set) -> list:
    problems = []
    ids = [s["slide_id"] for s in value.get("slides") or []]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        problems.append(f"slide_id {dup!r} is used more than once")
    covered = set()
    questions = {i for i, item in chapter["items"].items() if item["kind"] == "question"}
    for slide in value.get("slides") or []:
        sid = slide["slide_id"]
        if not slide["source_item_ids"]:
            problems.append(f"slide {sid}: every slide needs its source items (S7-01)")
        for iid in slide["source_item_ids"]:
            if iid not in chapter["items"]:
                problems.append(f"slide {sid}: unknown source item {iid!r}")
            covered.add(iid)
        for iid in slide["pyq_item_ids"]:
            if iid not in questions:
                problems.append(f"slide {sid}: {iid!r} is not a question item of the chapter")
        for key in ("question", "essence", "answer"):
            if not slide[key].strip():
                problems.append(f"slide {sid}: {key} is empty")
        v = slide["visual"]
        if v["type"] == "flow" and len(v["steps"]) < 2:
            problems.append(f"slide {sid}: a flow needs at least two steps")
        if v["type"] == "timeline" and len(v["events"]) < 2:
            problems.append(f"slide {sid}: a timeline needs at least two events")
        if v["type"] == "difference_table":
            if len(v["columns"]) < 2 or not v["rows"]:
                problems.append(f"slide {sid}: a difference table needs columns and rows")
            for row in v["rows"]:
                if len(row["cells"]) != len(v["columns"]):
                    problems.append(f"slide {sid}: row {row['label']!r} has {len(row['cells'])} cells for {len(v['columns'])} columns")
        if v["type"] == "chart" and len(v["series"]) < 2:
            problems.append(f"slide {sid}: a chart needs at least two values")
        if v["type"] in ("relationship", "concept_map", "tree", "labelled_list") and not v["nodes"]:
            problems.append(f"slide {sid}: a {v['type']} needs nodes")
        node_ids = {n["id"] for n in v["nodes"]}
        for n in v["nodes"]:
            if n["parent_id"] and n["parent_id"] not in node_ids:
                problems.append(f"slide {sid}: node {n['id']} has unknown parent {n['parent_id']!r}")
        for e in v["edges"]:
            if e["from_id"] not in node_ids or e["to_id"] not in node_ids:
                problems.append(f"slide {sid}: an edge uses an unknown node")
    missing = sorted(teachable - covered)
    if missing:
        problems.append(f"{len(missing)} teachable items are the source of no slide (S7-01): {', '.join(missing[:40])}")
    if not value.get("slides"):
        problems.append("there are no slides")
    return problems


def apply_patch(previous: dict, patch: dict) -> dict:
    replace = {s["slide_id"]: s for s in patch.get("replace_slides") or []}
    removed = set(patch.get("remove_slide_ids") or [])
    slides = [replace.pop(s["slide_id"], s) for s in previous.get("slides") or [] if s["slide_id"] not in removed]
    slides.extend(replace.values())
    return dict(previous, notes=patch.get("notes") or previous.get("notes"), slides=slides)


def concept_step(course: Course, chapter, concept, *, rulebook, max_rounds=3) -> Step:
    payload, teachable = _concept_input(chapter, concept)
    text = json.dumps(payload, ensure_ascii=False)
    system = fmt(ROLE, course, rules=rulebook.instructions(SECTION))
    user = f"Chapter: {course.title}. Concept {concept['concept_id']}.\nConcept, items and teacher questions (JSON):\n{text}\n\nReply with the notes JSON."
    review_system = fmt(REVIEW_ROLE, course, review_rules=rulebook.reviewer_instructions(), checklist=checklist_text(rulebook, SECTION))

    def review_user(value):
        return (f"Chapter: {course.title}. Concept {concept['concept_id']}.\nConcept, items and teacher questions (JSON):\n{text}\n\n"
                f"The notes to review (JSON):\n{json.dumps(value, ensure_ascii=False)}")

    return Step(section=SECTION, unit=f"concept-{concept['concept_id']}", instructions_version=VERSION, system=system, user=user,
                schema=NOTES_OUT_SCHEMA, check=lambda value: check_slides(value, chapter, teachable), review_system=review_system,
                review_user=review_user, review_schema=REVIEW_SCHEMA, review_problems=review_problems, patch_schema=PATCH_SCHEMA,
                apply_patch=apply_patch, patch_hint=PATCH_HINT, max_rounds=max_rounds)


def run_notes(chapter: dict, course: Course, runner, out_dir, *, workers: int = 4, max_rounds: int = 3):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    m = chapter.get("map") or {}
    concepts = {c["concept_id"]: c for c in m.get("concepts", [])}
    order = [cid for cid in m.get("teaching_order", []) if cid in concepts] or list(concepts)
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        results = list(pool.map(lambda cid: runner.run(concept_step(course, chapter, concepts[cid], rulebook=runner.rulebook,
                                                                    max_rounds=max_rounds)), order))
    notes = {
        "schema": "bie.brain.notes/1",
        "course": chapter["course"],
        "rulebook_version": runner.rulebook.version,
        "maker_route": runner.maker,
        "reviewer_route": runner.reviewer,
        "concepts": [{
            "concept_id": cid, "name": concepts[cid]["name"], "status": result.status, "rounds": len(result.rounds),
            "slides": (result.output or {}).get("slides", []),
            "last_problems": (result.rounds[-1].get("code_problems") or []) + (result.rounds[-1].get("review_problems") or [])
            if result.rounds and not result.passed else [],
            "record": Path(result.record_path).name if result.record_path else None, "cost_usd": result.cost_usd,
        } for cid, result in zip(order, results)],
        "items": {iid: {"page": item["page"], "content": item["content"], "kind": item["kind"]}
                  for iid, item in chapter["items"].items()},
    }
    slides = [s for c in notes["concepts"] for s in c["slides"]]
    notes["cost_usd"] = round(sum(c["cost_usd"] for c in notes["concepts"]), 6)
    notes["quality"] = {"concepts": len(order), "concepts_passed": sum(1 for c in notes["concepts"] if c["status"] == "passed"),
                        "slides": len(slides), "visuals": sum(1 for s in slides if s["visual"]["type"] != "none"),
                        "pyq_links": sum(len(s["pyq_item_ids"]) for s in slides), "cost_usd": notes["cost_usd"]}
    (out / "notes.json").write_text(json.dumps(notes, ensure_ascii=False, indent=1), encoding="utf-8")
    from .notes_render import render_notes_html
    (out / "NOTES.html").write_text(render_notes_html(notes), encoding="utf-8")
    return notes
