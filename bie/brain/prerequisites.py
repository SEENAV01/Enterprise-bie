"""Trim a chapter map's prerequisites to what the chapter directly needs (Navin, 23 October 2026; S1-12, S2-03).

The tissue map of 23 October listed 30 prerequisites, most of them background to other prerequisites. Navin's rule:
only what this chapter directly needs, never a prerequisite of a prerequisite, taught in one short "pehle yeh jaan lo"
video (5-8 minutes). Maps made from now on follow the rule in the connect step; an older map is trimmed here once,
before its lesson is planned: the maker keeps, merges or drops every current prerequisite (each with a reason), the
independent reviewer checks that nothing directly needed was dropped and nothing kept is only background, and BIE's
code checks the result (at most 8, each needed by named chapter concepts, every current prerequisite kept, merged
or dropped exactly once). Nothing else in the map changes; the naksha is built again, so its sha256 changes.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from . import cards
from . import content_types as ct
from . import naksha as naksha_module
from .common import S, arr as _arr, checklist_text as _checklist_text, obj as _obj, review_problems
from .runner import NOTES_SCHEMA, Step
from .understanding import (CONNECT, CONNECT_REVIEW_SCHEMA, DEFAULT_OUTPUT_TOKENS, MAX_PREREQUISITES, chapter_id, fmt,
                            prerequisite_problems, render_markdown)

TASK = "trim_prerequisites"
VERSION = "prerequisites-trim/1"
SCHEMA_ID = "bie.brain.prerequisites-trim/1"
SCHEMA = _obj({
    "notes": NOTES_SCHEMA,
    "prerequisites": _arr(_obj({"name": S, "why_needed": S, "needed_for": _arr(S),
                                "basis": {"type": "string", "enum": ["book", "outside"]}, "from_ids": _arr(S)})),
    "dropped": _arr(_obj({"id": S, "reason": S})),
})

ROLE = """You are BIE's book-understanding section: an expert teacher of {subject} for {learners} preparing for {exam}. The chapter
map of this chapter lists more prerequisites than the chapter directly needs. Keep only what a student must already understand to
follow this chapter's concepts, so that BIE can teach them in one short video before the chapter."""

HOW = """For a trim_prerequisites card:
- card.parts are the chapter map's current prerequisites (part_id = id "pre1", "pre2" ...); card.coverage.must_cover lists them all:
  each id must be in the from_ids of exactly one kept prerequisite or in dropped.
- The source lists the chapter's concepts (id | name | type | core explanation) and the current prerequisites
  (id | name | basis | needed for | why).
How to fill the JSON:
- notes: brief notes for the reviewer: what the chapter needs, your main keep, merge and drop decisions with a reason each, what is
  uncertain.
- prerequisites: at most {max_prerequisites}. Only what a student must already understand to follow this chapter's concepts directly;
  never a prerequisite of a prerequisite (if A is needed only to understand prerequisite B, drop A or fold it into B in one simple
  line); merge overlapping ones. Each: name (short, in clear English), why_needed (one sentence), needed_for (the chapter concept ids
  that need it directly), basis ("book" or "outside"), from_ids (the current ids it keeps or merges).
- dropped: every current prerequisite that is not kept or merged, with the reason (only background for another prerequisite; taught
  in the chapter itself; not needed to follow the chapter; ...).
BIE teaches the kept prerequisites in one 5-8 minute "pehle yeh jaan lo" video, so each must be small and concrete.
Reply with the JSON object only."""

REVIEW_ROLE = """You are BIE's independent reviewer for the trimmed prerequisites of a chapter map. Another AI decided which of the
map's prerequisites a student directly needs before this chapter; you check its decisions against the concepts."""

REVIEW_HOW = """You also get the maker's notes. Report every problem with where it is (a prerequisite name or id), the fix and a severity
("blocking" or "minor", see R-01): a prerequisite the chapter directly needs that was dropped, a kept prerequisite that is only
background for another prerequisite (a chain), a merge that loses something needed, needed_for naming concepts that do not need it,
a name or reason a teacher would find unclear. verdict is "pass" when nothing is blocking. Fill your own brief notes first. Reply
with the JSON object only."""


def current(chapter: dict) -> list:
    """[(id, prerequisite)] of the map, "pre1", "pre2" ... in its order."""
    return [(f"pre{n}", p) for n, p in enumerate((chapter.get("map") or {}).get("prerequisites_to_teach") or [], 1)]


def needs_trim(chapter: dict) -> bool:
    """True when the map's prerequisites break S1-12 (too many, or not tied to chapter concepts)."""
    m = chapter.get("map") or {}
    known = {c["concept_id"] for c in m.get("concepts") or []}
    return bool(prerequisite_problems(m.get("prerequisites_to_teach") or [], known))


def check_trim(value: dict, chapter: dict) -> list:
    """Code checks: S1-12 on the kept list, and every current prerequisite kept, merged or dropped exactly once."""
    known = {c["concept_id"] for c in (chapter.get("map") or {}).get("concepts") or []}
    problems = prerequisite_problems(value.get("prerequisites") or [], known)
    ids = [pid for pid, _ in current(chapter)]
    used = [i for p in value.get("prerequisites") or [] for i in p.get("from_ids") or []] + \
           [d["id"] for d in value.get("dropped") or []]
    for pid in ids:
        if used.count(pid) != 1:
            problems.append(f"{pid} must be in exactly one kept prerequisite's from_ids or in dropped (it is in {used.count(pid)})")
    unknown = sorted(set(used) - set(ids))
    if unknown:
        problems.append(f"unknown prerequisite ids {unknown[:10]}")
    for p in value.get("prerequisites") or []:
        if not p.get("from_ids"):
            problems.append(f"prerequisite {p['name']!r}: from_ids must name the current prerequisites it keeps or merges")
    return problems


def trim_step(course, chapter: dict, *, rulebook, max_rounds=3, max_output_tokens=DEFAULT_OUTPUT_TOKENS) -> Step:
    types = ct.load()
    how = HOW.replace("{max_prerequisites}", str(MAX_PREREQUISITES))
    prefix = cards.build_prefix(section=CONNECT, task=TASK, version=1, schema_id=SCHEMA_ID, schema=SCHEMA,
                                role=fmt(ROLE, course), how=how, rulebook=rulebook, course=course, types=types)
    review_prefix = cards.build_prefix(section=CONNECT, task=TASK, version=1, schema_id="bie.brain.prerequisites-trim-review/1",
                                       schema=CONNECT_REVIEW_SCHEMA, role=REVIEW_ROLE, how=REVIEW_HOW, rulebook=rulebook,
                                       course=course, types=types, review=True, checklist=_checklist_text(rulebook, CONNECT))
    naksha = naksha_module.build(chapter, types)
    index = naksha_module.Index(naksha)
    prerequisites = current(chapter)
    parts = [cards.part(pid, [pid], ct.NONE, naksha_module.short(p["name"], 90), types=types) for pid, p in prerequisites]
    card = cards.make(
        prefix=prefix, chapter_id=chapter_id(course),
        unit={"unit_id": "prerequisites", "title": course.title, "pages": sorted({row[2] for row in naksha["items"]}) or [1]},
        parts=parts, rules=sorted(r.id for r in rulebook.for_section(CONNECT)), mode="full", max_output_tokens=max_output_tokens,
        must_cover=[pid for pid, _ in prerequisites], claim_field="prerequisites[].from_ids or dropped[].id", may_skip=[],
        map_slice=naksha_module.concept_slice(naksha, index=index), before="", after="", block_ids=[], page_images=[])
    cards.require_valid(card, prefix=prefix, rulebook=rulebook, types=types,
                        known_ids=set(index.concepts) | {pid for pid, _ in prerequisites})
    concepts = "\n".join(f"{c['concept_id']} | {c['name']} | {c.get('content_type', '')} | "
                         f"{naksha_module.short(c.get('core_explanation', ''), 220)}"
                         for c in (chapter.get("map") or {}).get("concepts") or [])
    rows = "\n".join(f"{pid} | {p['name']} | {p.get('basis', '')} | {', '.join(p.get('needed_for') or [])} | {p.get('why_needed', '')}"
                     for pid, p in prerequisites)
    source = (f"Concepts of the chapter (id | name | type | core explanation):\n{concepts}\n\n"
              f"Current prerequisites (id | name | basis | needed for | why):\n{rows}")
    user = cards.user_message(card, source, (), "Answer the card with the trimmed prerequisites JSON.")

    def review_user(value):
        return cards.user_message(card, source + "\n\nThe trimmed prerequisites to review (JSON):\n" + cards.compact(value),
                                  (), "Review the trimmed prerequisites; reply with the review JSON.")

    return Step(section=CONNECT, unit="prerequisites", instructions_version=VERSION, system=prefix.text, user=user, schema=SCHEMA,
                check=lambda value: check_trim(value, chapter), review_system=review_prefix.text, review_user=review_user,
                review_schema=CONNECT_REVIEW_SCHEMA, review_problems=review_problems, max_rounds=max_rounds, card=card)


def apply_trim(chapter: dict, value: dict, *, record: str | None = None, rulebook_version: str = "") -> dict:
    """A new chapter map with the trimmed prerequisites (the rest unchanged) and the trim recorded."""
    out = copy.deepcopy(chapter)
    before = current(chapter)
    out["map"]["prerequisites_to_teach"] = [{k: p[k] for k in ("name", "why_needed", "needed_for", "basis", "from_ids")}
                                            for p in value.get("prerequisites") or []]
    out["prerequisite_trim"] = {"before": [{"id": pid, "name": p["name"]} for pid, p in before],
                                "dropped": value.get("dropped") or [], "record": record, "rulebook_version": rulebook_version,
                                "rule": "S1-12 and S2-03, Navin, 23 October 2026"}
    built = naksha_module.build(out)
    out["naksha"] = dict(naksha_module.size(built), sha256=built["sha256"], status="passed")
    return out


def run_trim(chapter: dict, course, runner, out_dir, *, max_rounds: int = 3) -> tuple:
    """(chapter, summary): the chapter itself when its prerequisites already keep S1-12; otherwise the trim step's result,
    written as chapter_map.json, naksha.json and MAP.md in ``out_dir``. A trim that does not pass leaves the map unchanged."""
    if not needs_trim(chapter):
        return chapter, {"status": "not needed", "count": len(current(chapter))}
    result = runner.run(trim_step(course, chapter, rulebook=runner.rulebook, max_rounds=max_rounds))
    summary = {"status": result.status, "before": len(current(chapter)), "rounds": len(result.rounds),
               "record": Path(result.record_path).name if result.record_path else None, "cost_usd": result.cost_usd}
    if not result.passed:
        return chapter, summary
    trimmed = apply_trim(chapter, result.output, record=summary["record"], rulebook_version=runner.rulebook.version)
    summary["after"] = len(trimmed["map"]["prerequisites_to_teach"])
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "chapter_map.json").write_text(json.dumps(trimmed, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "naksha.json").write_text(json.dumps(naksha_module.build(trimmed), ensure_ascii=False, separators=(",", ":")),
                                     encoding="utf-8")
    (out / "MAP.md").write_text(render_markdown(trimmed), encoding="utf-8")
    return trimmed, summary
