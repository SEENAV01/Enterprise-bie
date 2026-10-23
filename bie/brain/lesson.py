"""Section 2 · Lesson plan and teacher script.

From the chapter map (Section 1) BIE plans the chapter's videos like the best teacher (how many, which
concepts, prerequisites taught first, length from content) and then writes each video's spoken teacher
script in beats, in Navin's Hinglish. Every beat claims which chapter-map items it covers and which teacher
questions it answers; BIE's code checks that every item and every question of the video is covered, and the
independent reviewer checks that the claims are true and the flow is a real teacher's. Every step runs
through ``SectionRunner``.

Since Task 045 both steps run on task cards (``bie/brain/cards.py``) built from the naksha, never from the
whole chapter map: the plan card carries the concept layer, a script card carries its video's items grouped
into parts by content type, with the type's required questions. The script answers the universal frame for
every part (the process, how, when, the conditions, the atmosphere) and teaches each part through the
teaching pattern of its type, step by step; BIE's code checks the frame, every pattern step, ``must_cover``
both ways, Navin's spoken Hinglish, and (through the old PED engine) objective coverage, load per beat,
prerequisites and length.

Outputs (``run_lesson``): ``lesson_plan.json`` (plan plus scripts, what the director consumes),
``SCRIPT.md`` (all scripts, readable), ``scripts/<video id>.md`` (one readable page per video), one process
record per step under ``records/``.

Resume (``previous_lesson``): a run that stopped (the plan's own limit, the rupee cap) continues from its
``lesson_plan.json``. The plan and every script that passed are reused when the chapter map is the same (same
naksha) and they still pass today's code checks; everything else runs again.
"""
from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import cards
from . import content_types as ct
from . import engines
from . import hinglish
from . import naksha as naksha_module
from .common import SEVERITY, S, arr as _arr, checklist_text as _checklist_text, fmt as _fmt, obj as _obj, review_problems
from .runner import NOTES_SCHEMA, Step
from .understanding import DEFAULT_OUTPUT_TOKENS, Course, chapter_id

SECTION = "lesson"
PLAN_VERSION = "lesson-plan/2"
SCRIPT_VERSION = "lesson-script/2"
PLAN_SCHEMA_ID = "bie.brain.lesson-plan/2"
SCRIPT_SCHEMA_ID = "bie.brain.lesson-script/2"
PURPOSES = ["hook", "prerequisite", "explain", "example", "analogy", "story", "compare", "process_walkthrough",
            "misconception", "exam_tip", "question_to_student", "recap", "transition"]
DEVANAGARI = re.compile(r"[ऀ-ॿ]")
DEVANAGARI_DIGIT = re.compile(r"[०-९]")
SENTENCE_END = re.compile(r"[।?!.]+")
LONGEST_SENTENCE = 40        # words; Navin's style is short spoken sentences (S2-04)
FRAME = ("process", "how", "when", "conditions", "atmosphere")
# The frame questions a type cannot answer with "n/a" (S3-01 asks all five of every topic).
FRAME_NEEDS = {"process": ("process", "how", "when", "conditions"), "timeline": ("when", "conditions", "atmosphere"),
               "cause_effect": ("how", "conditions"), "structure": ("how",), "figure": ("how",)}

PLAN_SCHEMA = _obj({
    "notes": NOTES_SCHEMA,
    "videos": _arr(_obj({
        "video_id": S,
        "title": S,
        "goal": S,
        "concept_ids": _arr(S),
        "prerequisites_taught": _arr(S),
        "opening_hook": S,
        "story_or_analogy": S,
        "estimated_minutes": {"type": "integer"},
        "why_this_unit": S,
    })),
    "chapter_flow": S,
})
FRAME_SCHEMA = _obj({key: S for key in FRAME})
PART_SCHEMA = _obj({"part_id": S, "frame": FRAME_SCHEMA})
BEAT_SCHEMA = _obj({
    "beat_id": S,
    "part_id": S,
    "step": {"type": "integer"},
    "purpose": {"type": "string", "enum": PURPOSES},
    "say": S,
    "covers_item_ids": _arr(S),
    "answers": _arr(S),
    "on_screen": S,
    "basis": {"type": "string", "enum": ["book", "outside", "mixed"]},
})
SCRIPT_SCHEMA = _obj({
    "notes": NOTES_SCHEMA,
    "title": S,
    "parts": _arr(PART_SCHEMA),
    "beats": _arr(BEAT_SCHEMA),
})
SCRIPT_PATCH_SCHEMA = _obj({
    "notes": NOTES_SCHEMA,
    "replace_parts": _arr(PART_SCHEMA),
    "replace_beats": _arr(BEAT_SCHEMA),
    "insert_beats": _arr(_obj({"after_beat_id": S, "beat": BEAT_SCHEMA})),
    "remove_beat_ids": _arr(S),
})
SCRIPT_PATCH_HINT = ("Reply with a patch, not the whole script: replace_parts = parts whose frame changes (same part_id), replace_beats = "
                     "complete corrected beats (same beat_id), insert_beats = new beats with the beat_id they follow (\"\" for the very "
                     "start), remove_beat_ids = beats to delete.")
REVIEW_SCHEMA = _obj({
    "notes": NOTES_SCHEMA,
    "verdict": {"type": "string", "enum": ["pass", "fail"]},
    "problems": _arr(_obj({"where": S, "problem": S, "fix": S, "severity": SEVERITY})),
    "checklist": _arr(_obj({"rule_id": S, "met": {"type": "boolean"}, "note": S})),
})


def apply_script_patch(previous: dict, patch: dict) -> dict:
    replace = {b["beat_id"]: b for b in patch.get("replace_beats") or []}
    removed = set(patch.get("remove_beat_ids") or [])
    beats = [replace.get(b["beat_id"], b) for b in previous.get("beats") or [] if b["beat_id"] not in removed]
    for entry in patch.get("insert_beats") or []:
        ids = [b["beat_id"] for b in beats]
        at = ids.index(entry["after_beat_id"]) + 1 if entry["after_beat_id"] in ids else (0 if not entry["after_beat_id"] else len(beats))
        beats.insert(at, entry["beat"])
    frames = {p["part_id"]: p for p in patch.get("replace_parts") or []}
    parts = [frames.pop(p["part_id"], p) for p in previous.get("parts") or []] + list(frames.values())
    return dict(previous, notes=patch.get("notes") or previous.get("notes"), beats=beats, parts=parts)


PLAN_ROLE = """You are BIE's lesson section: the best teacher of {subject} for {learners} preparing for {exam}, planning the video
lessons of one chapter from BIE's chapter map. Students learn only from these videos, so the plan must make the whole chapter
understandable, starting from what they already know."""

PLAN_HOW = """For a plan_videos card:
- card.parts are the chapter's concepts (part_id = concept id) with their content type; card.coverage.must_cover lists every concept id,
  and each must be in the concept_ids of some video. card.context.map_slice has one row per concept: [concept id, type, pages, name].
- The source has the chapter summary, how the concepts link ([from, link, to]: pre = prerequisite, part, kind, cause, compare, seq =
  sequence, example, test), the prerequisites to teach, BIE's teaching order and the exam focus.
How to fill the JSON:
- notes: brief notes for the reviewer: what the chapter is about, the key questions the plan must serve, your main decisions with a
  reason each, what is uncertain.
- videos: in teaching order. video_id "v1", "v2" ...; title in the learner language; goal = what the student will understand after it;
  concept_ids = the concept ids taught in it, in order (every concept in some video); prerequisites_taught = names from the prerequisites
  to teach that this video teaches first, spelled exactly as given; opening_hook = a real-life question, puzzle or surprise that opens it;
  story_or_analogy = the story or analogy that genuinely helps, or "" if none fits; estimated_minutes from the content (a teacher
  explaining every item and question at a natural pace), never a fixed length; why_this_unit = why these concepts belong together.
- chapter_flow: how the videos build on each other.
Reply with the JSON object only."""

SCRIPT_ROLE = """You are BIE's lesson section writing what the teacher says in one video lesson: you are the best teacher of {subject}
for {learners} preparing for {exam}, speaking to one student. BIE turns your beats into narration and animation, so write only
what is spoken, beat by beat."""

SCRIPT_HOW = """For a write_script card:
- card.parts are this video's parts: each has item ids, one content type and the questions it must answer. The source gives every item's
  full content and its teacher questions with ids ("p003-i4#q2") and answers from BIE's chapter map; teach from them.
- card.coverage.must_cover lists every item this video must teach: each must be in covers_item_ids of a beat that really explains it.
  may_skip lists items you may leave out (not teachable). card.context.map_slice shows the related concepts for context only.
How to fill the JSON:
- notes: brief notes for the reviewer: what this video is about, the key questions it must answer, your main decisions (order,
  hook, analogy, where prerequisites are taught) with a reason each, what is uncertain.
- title: the video title in the learner language.
- parts: one entry per card part, with the universal frame of that part (S3-01), each in one or two lines of clear English for BIE:
  process (what happens or what the thing does), how (how it works or happens), when (when, in what order, under which timing),
  conditions (what must be true for it, or what changes it), atmosphere (the setting and situation a student should picture). Write
  "n/a: " and the reason only where a question truly does not apply to that part.
- beats: the whole video in order. beat_id "b1", "b2" ...; part_id = the card part this beat teaches ("" for the opening hook, a
  prerequisite taught first, a transition or the final recap); step = the number of the teaching-pattern step of that part's content type
  that this beat performs (see the content types above; 0 when part_id is "" and for an exam-question part, whose type is "none");
  every step of a part's pattern must appear, in order;
  purpose (hook, prerequisite, explain, example, analogy, story, compare, process_walkthrough, misconception, exam_tip,
  question_to_student, recap, transition); say = the exact spoken words, one to four short spoken sentences in Navin's Hinglish (S2-04):
  mixed script: Hindi words in Devanagari, English words (above all the book's technical terms, spelled as the book spells them) in
  Roman, as in "आज हम tissue के बारे में पढ़ेंगे"; a Hindi word that is not in the simple everyday list below gets its English word in
  brackets right after it, as in "सतह (surface)" (BIE's code checks it, shows the bracket on screen and makes the voice say
  "सतह, यानी surface"); never write an English term in Devanagari or a Hindi word in Roman; numbers as digits; addressed to one student; covers_item_ids = the item ids this beat really explains; answers = the teacher question ids this beat
  really answers; on_screen = what the student should see while hearing it (for the director); basis = book, outside or mixed.
Every item in must_cover and every teacher question listed for this video must be covered by some beat. A beat introduces at most a
few new items: BIE's code measures the load of every beat and asks you to split heavy ones. Reply with the JSON object only."""

REVIEW_ROLE = """You are BIE's independent reviewer for the lesson section. Another AI wrote the work below from BIE's task card. You check
it as Navin would: is this how the best teacher would teach it?"""

REVIEW_HOW = """You also get the maker's notes. Report every problem with where it is (video, part or beat id), what is wrong, the fix and a
severity ("blocking" or "minor", see R-01): an item or teacher question not really covered (even if claimed), a part whose frame is
empty or wrong, a teaching-pattern step that is only named and not done, a prerequisite named but not taught, a jump a student cannot
follow, an analogy that does not fit, a fact wrong at this level, language that is not natural spoken Hinglish, beats that read out
lists. Precision beyond the level of a standard textbook for these learners is minor.
verdict is "pass" when nothing is blocking. Fill your own brief notes first. Reply with the JSON object only."""


def question_ids(item: dict):
    return [f"{item['item_id']}#q{n}" for n in range(1, len(item.get("teacher_understanding") or []) + 1)]


def _concepts(chapter):
    return {c["concept_id"]: c for c in (chapter.get("map") or {}).get("concepts", [])}


def chapter_naksha(chapter: dict) -> dict:
    """The naksha of a chapter map (built again for maps made before Task 045, whose types are converted)."""
    return naksha_module.build(chapter)


def check_plan(value, chapter):
    problems = []
    concepts = _concepts(chapter)
    ids = [v["video_id"] for v in value.get("videos") or []]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        problems.append(f"video_id {dup!r} is used more than once")
    taught = set()
    for video in value.get("videos") or []:
        for cid in video["concept_ids"]:
            if cid not in concepts:
                problems.append(f"video {video['video_id']}: unknown concept {cid!r}")
            taught.add(cid)
        if video["estimated_minutes"] < 1:
            problems.append(f"video {video['video_id']}: estimated_minutes must be at least 1")
        if not video["concept_ids"]:
            problems.append(f"video {video['video_id']}: teaches no concept")
    for cid in sorted(set(concepts) - taught):
        problems.append(f"concept {cid} ({concepts[cid]['name']}) is in no video (S2-01)")
    problems += engines.plan_checks(value.get("videos") or [], list(concepts.values()),
                                    (chapter.get("map") or {}).get("prerequisites_to_teach", []))[0]
    if not value.get("videos"):
        problems.append("the plan has no videos")
    return problems


def video_scope(chapter, video):
    """The items and teacher questions a video must cover."""
    concepts = _concepts(chapter)
    item_ids = []
    for cid in video["concept_ids"]:
        for iid in (concepts.get(cid) or {}).get("item_ids", []):
            if iid in chapter["items"] and iid not in item_ids:
                item_ids.append(iid)
    items = [chapter["items"][i] for i in item_ids]
    questions = [qid for item in items if item.get("teachable") for qid in question_ids(item)]
    return items, questions


# ---------------------------------------------------------------- cards

def _prefix(course, rulebook, task, schema_id, schema, role, how, *, review=False):
    if review:
        return cards.build_prefix(section=SECTION, task=task, version=2, schema_id=schema_id, schema=schema, role=role,
                                  how=how, rulebook=rulebook, course=course, patterns=True, review=True,
                                  checklist=_checklist_text(rulebook, SECTION))
    return cards.build_prefix(section=SECTION, task=task, version=2, schema_id=schema_id, schema=schema,
                              role=_fmt(role, course), how=how, rulebook=rulebook, course=course, patterns=True)


def _rules(rulebook):
    return sorted(r.id for r in rulebook.for_section(SECTION))


def _known(chapter, index):
    return set(chapter["items"]) | set(index.concepts)


def plan_card(course, chapter, naksha, *, rulebook, prefix, max_output_tokens=DEFAULT_OUTPUT_TOKENS) -> dict:
    types = ct.load()
    index = naksha_module.Index(naksha)
    parts = []
    for cid, name, kind, item_ids in naksha["concepts"]:
        parts.append(cards.part(cid, item_ids or [cid], kind if kind in types.types else "facts_numbers",
                                naksha_module.short(name, 90), types=types))
    pages = sorted({row[2] for row in naksha["items"]})
    card = cards.make(
        prefix=prefix, chapter_id=chapter_id(course), unit={"unit_id": "plan", "title": course.title, "pages": pages},
        parts=parts or [cards.part("none", ["none"], "facts_numbers", "no concepts", types=types)], rules=_rules(rulebook),
        mode="full", max_output_tokens=max_output_tokens, must_cover=list(index.concepts), claim_field="videos[].concept_ids",
        may_skip=[], map_slice=naksha_module.concept_slice(naksha, index=index), before="", after="", block_ids=[], page_images=[])
    return cards.require_valid(card, prefix=prefix, rulebook=rulebook, known_ids=_known(chapter, index) | {"none"}, types=types)


def _plan_source(chapter, naksha) -> str:
    m = chapter.get("map") or {}
    links = "\n".join(f"{a} {link} {b}" for a, link, b in naksha["links"] if a in {c[0] for c in naksha["concepts"]})
    prereq = "\n".join(f"- {p['name']} · needed for {', '.join(p.get('needed_for') or [])} · {p.get('basis', '')} · {p.get('why_needed', '')}"
                       for p in m.get("prerequisites_to_teach") or [])
    focus = "\n".join(f"- {f['concept_id']}: {f['why']}" for f in m.get("exam_focus") or [])
    return (f"Chapter summary: {m.get('chapter_summary', '')}\n\nHow the concepts link (from link to):\n{links or '(none)'}\n\n"
            f"Prerequisites to teach (name · needed for · basis · why):\n{prereq or '(none)'}\n\n"
            f"BIE's teaching order: {', '.join(naksha['order'])}\n\nExam focus:\n{focus or '(none)'}")


def script_parts(chapter, naksha, video, types=None) -> list:
    """The card parts of one video: per concept, its teachable items grouped by content type, in reading order, then
    its exam questions (PYQs, type ``none``: answered as exam tips once the concept is taught)."""
    types = types or ct.load()
    index = naksha_module.Index(naksha)
    concepts = _concepts(chapter)
    parts, used = [], set()
    for cid in video["concept_ids"]:
        groups, pyqs = {}, []
        for iid in (concepts.get(cid) or {}).get("item_ids", []):
            item = chapter["items"].get(iid, {})
            if iid in used or iid not in index.items or not item.get("teachable"):
                continue
            kind = index.items[iid][1]
            if item.get("kind") in ct.ROLE_KINDS:
                pyqs.append(iid)
            elif kind in types.types:
                groups.setdefault(kind, []).append(iid)
            else:
                continue
            used.add(iid)
        name = naksha_module.short((concepts.get(cid) or {}).get("name", cid), 80)
        asks_of = lambda ids: [q["ask"] for i in ids for q in chapter["items"][i].get("teacher_understanding") or []]
        for n, (kind, ids) in enumerate(groups.items(), 1):
            parts.append(cards.part(f"{cid}.{n}", ids, kind, f"{name}: teach these {kind} items through the {kind} pattern",
                                    questions=asks_of(ids), types=types))
        if pyqs:
            parts.append(cards.part(f"{cid}.q", pyqs, ct.NONE, f"{name}: exam questions (PYQ); answer each as an exam tip once "
                                    "the concept is taught (step 0)", questions=asks_of(pyqs), types=types))
    return parts


def script_card(course, chapter, naksha, plan, video, *, rulebook, prefix, max_output_tokens=DEFAULT_OUTPUT_TOKENS) -> dict:
    types = ct.load()
    index = naksha_module.Index(naksha)
    items, _ = video_scope(chapter, video)
    parts = script_parts(chapter, naksha, video, types)
    must = [i for p in parts for i in p["item_ids"]]
    skip = [{"item_id": i["item_id"], "reason": "not teachable (heading or container)"} for i in items if not i.get("teachable")]
    order = [v["video_id"] for v in plan["videos"]]
    position = order.index(video["video_id"])
    card = cards.make(
        prefix=prefix, chapter_id=chapter_id(course),
        unit={"unit_id": video["video_id"], "title": video["title"], "pages": sorted({i["page"] for i in items})},
        parts=parts or [cards.part("none", [video["concept_ids"][0]], "facts_numbers", "no teachable items", types=types)],
        rules=_rules(rulebook), mode="full", max_output_tokens=max_output_tokens, must_cover=must,
        claim_field="beats[].covers_item_ids", may_skip=skip, map_slice=naksha_module.slice_rows(naksha, must, index=index),
        before=plan["videos"][position - 1]["title"] if position else "",
        after=plan["videos"][position + 1]["title"] if position + 1 < len(order) else "",
        block_ids=[b for i in items for b in i.get("block_ids") or []], page_images=[])
    return cards.require_valid(card, prefix=prefix, rulebook=rulebook, known_ids=_known(chapter, index), types=types)


def _script_source(chapter, video) -> str:
    items, _ = video_scope(chapter, video)
    prereq = [p for p in (chapter.get("map") or {}).get("prerequisites_to_teach", [])
              if p["name"].strip().lower() in {x.strip().lower() for x in video["prerequisites_taught"]}]
    lines = [f"Video {video['video_id']}: {video['title']}", f"Goal: {video['goal']}", f"Opening hook: {video['opening_hook']}",
             f"Story or analogy: {video['story_or_analogy'] or '(none)'}", f"Planned minutes: {video['estimated_minutes']}"]
    if prereq:
        lines.append("Prerequisites to teach first in this video (name · basis · why):")
        lines += [f"- {p['name']} · {p['basis']} · {p['why_needed']}" for p in prereq]
    lines.append("\nItems (item id | page | kind | type | content), each with its teacher questions "
                 "(question id | ask | question → answer | basis):")
    for item in items:
        content = re.sub(r"\s+", " ", item.get("content", "")).strip()
        lines.append(f"{item['item_id']} | {item['page']} | {item['kind']} | {item.get('content_type', '')} | {content}")
        for qid, qa in zip(question_ids(item), item.get("teacher_understanding") or []):
            lines.append(f"  {qid} | {qa['ask']} | {qa['question']} → {qa['answer']} | {qa['basis']}")
    return "\n".join(lines)


# ---------------------------------------------------------------- script checks

def spoken_problems(beats, language) -> list:
    """Navin's spoken Hinglish (S2-04), as far as code can see it."""
    problems = []
    if language.strip().lower() in ("hinglish", "hindi"):
        hindi = sum(1 for b in beats if DEVANAGARI.search(b["say"]))
        if beats and hindi < 0.8 * len(beats):
            problems.append(f"only {hindi} of {len(beats)} beats are written in Devanagari Hindi; write spoken Hinglish (S2-04)")
        digits = [b["beat_id"] for b in beats if DEVANAGARI_DIGIT.search(b["say"])]
        if digits:
            problems.append(f"beats {', '.join(digits[:10])} write numbers in Devanagari digits; write numbers as digits 0-9 (S2-04)")
        for b in beats:
            hard = hinglish.difficult_words(b["say"])
            if hard:
                problems.append(f"beat {b['beat_id']}: the Hindi words {hard[:8]} are not simple everyday words; put the English "
                                f"word in brackets right after each, as in \"सतह (surface)\", or use a simpler word (S2-04)")
            for bad in hinglish.bracket_problems(b["say"]):
                problems.append(f"beat {b['beat_id']}: {bad} (S2-04)")
            roman = hinglish.roman_hindi(b["say"])
            if roman:
                problems.append(f"beat {b['beat_id']}: the Hindi words {roman} are written in Roman; write Hindi words in "
                                "Devanagari (S2-04)")
    long = [b["beat_id"] for b in beats
            if any(len(s.split()) > LONGEST_SENTENCE for s in SENTENCE_END.split(b["say"]))]
    if long:
        problems.append(f"beats {', '.join(long[:10])} have a sentence longer than {LONGEST_SENTENCE} words; "
                        "speak in short sentences (S2-04)")
    return problems


def frame_problems(value, card, types=None) -> tuple:
    """(problems, observed): the universal frame of every part and every teaching-pattern step, from the card."""
    types = types or ct.load()
    problems, observed = [], {"pattern_order": []}
    card_parts = {p["part_id"]: p for p in card["parts"]}
    frames = {p["part_id"]: p["frame"] for p in value.get("parts") or []}
    for pid, part in card_parts.items():
        frame = frames.get(pid)
        if frame is None:
            problems.append(f"part {pid}: the universal frame is missing (process, how, when, conditions, atmosphere; S3-01)")
            continue
        empty = [k for k in FRAME if not frame.get(k, "").strip()]
        if empty:
            problems.append(f"part {pid}: frame fields {empty} are empty; answer them or write 'n/a: ' with the reason")
        needed = [k for k in FRAME_NEEDS.get(part["type"], ()) if frame.get(k, "").strip().lower().startswith("n/a")]
        if needed:
            problems.append(f"part {pid}: a {part['type']} part must answer {needed} in its frame, not 'n/a'")
    for pid in sorted(set(frames) - set(card_parts)):
        problems.append(f"parts: {pid!r} is not a part of the card")
    steps = {}
    for beat in value.get("beats") or []:
        pid = beat.get("part_id") or ""
        if not pid:
            continue
        if pid not in card_parts:
            problems.append(f"beat {beat['beat_id']}: part_id {pid!r} is not a part of the card")
            continue
        pattern = types.pattern(card_parts[pid]["type"])
        if not pattern:
            if beat.get("step", 0) != 0:
                problems.append(f"beat {beat['beat_id']}: part {pid} has no teaching pattern, so its step is 0")
            continue
        if not 1 <= beat.get("step", 0) <= len(pattern):
            problems.append(f"beat {beat['beat_id']}: step {beat.get('step')} is not a step of the {card_parts[pid]['type']} "
                            f"pattern (1-{len(pattern)})")
            continue
        steps.setdefault(pid, []).append(beat["step"])
    for pid, part in card_parts.items():
        pattern = types.pattern(part["type"])
        done = steps.get(pid, [])
        missing = [n for n in range(1, len(pattern) + 1) if n not in done]
        if missing:
            names = "; ".join(f"{n}) {pattern[n - 1]}" for n in missing)
            problems.append(f"part {pid} ({part['type']}): teaching-pattern steps not taught: {names}")
        if done != sorted(done):
            observed["pattern_order"].append(pid)
    return problems, observed


def check_script(value, chapter, video, language, card=None):
    problems = []
    items, questions = video_scope(chapter, video)
    scope_items = {i["item_id"] for i in items}
    scope_questions = set(questions)
    beats = value.get("beats") or []
    ids = [b["beat_id"] for b in beats]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        problems.append(f"beat_id {dup!r} is used more than once")
    covered, answered = set(), set()
    for beat in beats:
        if not beat["say"].strip():
            problems.append(f"beat {beat['beat_id']}: say is empty")
        for iid in beat["covers_item_ids"]:
            if iid not in scope_items:
                problems.append(f"beat {beat['beat_id']}: item {iid!r} is not an item of this video")
            covered.add(iid)
        for qid in beat["answers"]:
            if qid not in scope_questions:
                problems.append(f"beat {beat['beat_id']}: {qid!r} is not a teacher question of this video")
            answered.add(qid)
    if card is not None:
        problems += cards.coverage_problems(card, [i for i in covered if i in scope_items], known=scope_items, rule="S2-02")
    else:
        teachable = [i["item_id"] for i in items if i.get("teachable")]
        missing_items = [i for i in teachable if i not in covered]
        if missing_items:
            problems.append(f"{len(missing_items)} items are covered by no beat (S2-02): {', '.join(missing_items[:40])}")
    missing_q = [q for q in questions if q not in answered]
    if missing_q:
        problems.append(f"{len(missing_q)} teacher questions are answered by no beat (S2-02): {', '.join(missing_q[:40])}")
    problems += spoken_problems(beats, language)
    if len(beats) < 3:
        problems.append("a video needs more than a couple of beats")
    if card is not None:
        problems += frame_problems(value, card)[0]
        problems += engines.script_checks(beats, card["coverage"]["must_cover"], planned_minutes=video.get("estimated_minutes"))[0]
    return problems


# ---------------------------------------------------------------- steps

def plan_step(course: Course, chapter, *, rulebook, max_rounds=3, naksha=None, max_output_tokens=DEFAULT_OUTPUT_TOKENS) -> Step:
    naksha = naksha or chapter_naksha(chapter)
    prefix = _prefix(course, rulebook, "plan_videos", PLAN_SCHEMA_ID, PLAN_SCHEMA, PLAN_ROLE, PLAN_HOW)
    review_prefix = _prefix(course, rulebook, "plan_videos", "bie.brain.lesson-plan-review/2", REVIEW_SCHEMA, REVIEW_ROLE,
                            REVIEW_HOW, review=True)
    card = plan_card(course, chapter, naksha, rulebook=rulebook, prefix=prefix, max_output_tokens=max_output_tokens)
    source = _plan_source(chapter, naksha)
    user = cards.user_message(card, source, (), "Answer the card with the lesson plan JSON.")

    def review_user(value):
        return cards.user_message(card, source + "\n\nThe lesson plan to review (JSON):\n" + json.dumps(value, ensure_ascii=False),
                                  (), "Review the plan; reply with the review JSON.")

    observe = lambda value: engines.plan_checks(value.get("videos") or [], [], (chapter.get("map") or {}).get(
        "prerequisites_to_teach", []))[1]
    return Step(section=SECTION, unit="plan", instructions_version=PLAN_VERSION, system=prefix.text, user=user, schema=PLAN_SCHEMA,
                check=lambda value: check_plan(value, chapter), review_system=review_prefix.text, review_user=review_user,
                review_schema=REVIEW_SCHEMA, review_problems=review_problems, max_rounds=max_rounds, card=card, observe=observe)


def script_prefixes(course, rulebook):
    how = SCRIPT_HOW + "\n\n" + hinglish.prefix_text()
    return (_prefix(course, rulebook, "write_script", SCRIPT_SCHEMA_ID, SCRIPT_SCHEMA, SCRIPT_ROLE, how),
            _prefix(course, rulebook, "write_script", "bie.brain.lesson-script-review/2", REVIEW_SCHEMA, REVIEW_ROLE, REVIEW_HOW,
                    review=True))


def script_step(course: Course, chapter, plan, video, *, rulebook, max_rounds=3, naksha=None, prefixes=None,
                max_output_tokens=DEFAULT_OUTPUT_TOKENS) -> Step:
    naksha = naksha or chapter_naksha(chapter)
    prefix, review_prefix = prefixes or script_prefixes(course, rulebook)
    card = script_card(course, chapter, naksha, plan, video, rulebook=rulebook, prefix=prefix, max_output_tokens=max_output_tokens)
    source = _script_source(chapter, video)
    user = cards.user_message(card, source, (), "Answer the card with the teacher script JSON.")

    def review_user(value):
        return cards.user_message(card, source + "\n\nThe teacher script to review (JSON):\n" + json.dumps(value, ensure_ascii=False),
                                  (), "Review the script; reply with the review JSON.")

    def observe(value):
        found = frame_problems(value, card)[1]
        found.update(engines.script_checks(value.get("beats") or [], card["coverage"]["must_cover"],
                                           planned_minutes=video.get("estimated_minutes"))[1])
        return found

    return Step(section=SECTION, unit=f"script-{video['video_id']}", instructions_version=SCRIPT_VERSION, system=prefix.text,
                user=user, schema=SCRIPT_SCHEMA, check=lambda value: check_script(value, chapter, video, course.language, card),
                review_system=review_prefix.text, review_user=review_user, review_schema=REVIEW_SCHEMA,
                review_problems=review_problems, patch_schema=SCRIPT_PATCH_SCHEMA, apply_patch=apply_script_patch,
                patch_hint=SCRIPT_PATCH_HINT, max_rounds=max_rounds, card=card, observe=observe)


def _script_value(video_entry: dict) -> dict:
    """A script as the maker wrote it, from a lesson_plan.json video (without the code-made subtitle and voice)."""
    beats = [{k: v for k, v in b.items() if k not in ("subtitle", "voice")} for b in video_entry.get("beats") or []]
    return {"notes": None, "title": video_entry.get("title", ""), "parts": video_entry.get("parts") or [], "beats": beats}


def reusable(previous: dict | None, chapter: dict, naksha: dict, course: Course, rulebook) -> tuple:
    """(plan or None, {video id: script value}, notes): what an earlier lesson run may give this one.

    Nothing is reused when the chapter map changed (another naksha). The plan is reused when it passed and still
    passes today's checks; a script only with its plan, when it passed and still passes today's checks on today's card.
    """
    notes = []
    if not previous:
        return None, {}, notes
    if previous.get("naksha_sha256") != naksha["sha256"]:
        return None, {}, ["the chapter map changed since the earlier run, so nothing is reused"]
    plan = previous.get("plan") or {}
    if previous.get("plan_status") != "passed" or not plan.get("videos"):
        return None, {}, ["the earlier plan did not pass, so the plan and the scripts run again"]
    problems = check_plan(plan, chapter)
    if problems:
        return None, {}, [f"the earlier plan fails today's checks ({problems[0][:120]}), so it runs again"]
    prefix = script_prefixes(course, rulebook)[0]
    scripts = {}
    by_id = {v["video_id"]: v for v in previous.get("videos") or []}
    for video in plan["videos"]:
        entry = by_id.get(video["video_id"])
        if not entry or entry.get("status") != "passed":
            continue
        card = script_card(course, chapter, naksha, plan, video, rulebook=rulebook, prefix=prefix)
        value = _script_value(entry)
        problems = check_script(value, chapter, video, course.language, card)
        if problems:
            notes.append(f"{video['video_id']} fails today's checks ({problems[0][:120]}), so it runs again")
            continue
        scripts[video["video_id"]] = value
    return plan, scripts, notes


def run_lesson(chapter: dict, course: Course, runner, out_dir, *, workers: int = 4, max_rounds: int = 3,
               max_output_tokens: int = DEFAULT_OUTPUT_TOKENS, previous_lesson: dict | None = None):
    from .runner import StepResult

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    naksha = chapter_naksha(chapter)
    book = cards.CardBook()                 # a card id is used once per run
    step = plan_step(course, chapter, rulebook=runner.rulebook, max_rounds=max_rounds, naksha=naksha,
                     max_output_tokens=max_output_tokens)
    book.add(step.card)
    old_plan, old_scripts, resume_notes = reusable(previous_lesson, chapter, naksha, course, runner.rulebook)
    if old_plan is not None:
        plan_result = StepResult(SECTION, "plan", "passed", dict(old_plan, notes=None), record_path=None)
    else:
        plan_result = runner.run(step)
    plan = plan_result.output or {"videos": []}
    videos = plan.get("videos") or [] if plan_result.passed else []
    prefixes = script_prefixes(course, runner.rulebook)
    steps = [script_step(course, chapter, plan, v, rulebook=runner.rulebook, max_rounds=max_rounds, naksha=naksha,
                         prefixes=prefixes, max_output_tokens=max_output_tokens) for v in videos]
    for step in steps:
        book.add(step.card)
    fresh = [(v, s) for v, s in zip(videos, steps) if v["video_id"] not in old_scripts]
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        done = dict(zip([v["video_id"] for v, _ in fresh], pool.map(runner.run, [s for _, s in fresh])))
    previous_videos = {v["video_id"]: v for v in (previous_lesson or {}).get("videos") or []}
    scripts = [done[v["video_id"]] if v["video_id"] in done else
               StepResult(SECTION, f"script-{v['video_id']}", "passed", old_scripts[v["video_id"]], record_path=None)
               for v in videos]
    lesson = {
        "schema": "bie.brain.lesson/2",
        "course": chapter["course"],
        "source_sha256": chapter.get("source_sha256"),
        "naksha_sha256": naksha["sha256"],
        "rulebook_version": runner.rulebook.version,
        "maker_route": runner.maker,
        "reviewer_route": runner.reviewer,
        "reviewer_independence": runner.independence,
        "plan_status": plan_result.status,
        "plan_reused": old_plan is not None,
        "resume_notes": resume_notes,
        "plan": {k: v for k, v in plan.items() if k != "notes"},
        "videos": [{
            "video_id": video["video_id"],
            "title": (result.output or {}).get("title") or video["title"],
            "status": result.status,
            "rounds": len(result.rounds) if video["video_id"] not in old_scripts else previous_videos[video["video_id"]]["rounds"],
            "reused": video["video_id"] in old_scripts,
            "parts": (result.output or {}).get("parts", []),
            "card_parts": [{k: p[k] for k in ("part_id", "type", "item_ids")} for p in step.card["parts"]],
            "beats": [dict(b, subtitle=hinglish.subtitle_text(b["say"]), voice=hinglish.voice_text(b["say"]))
                      for b in (result.output or {}).get("beats", [])],
            "checks": (result.rounds[-1].get("observed") if result.rounds else None) or {},
            "last_problems": (result.rounds[-1].get("code_problems") or []) + (result.rounds[-1].get("review_problems") or [])
            if result.rounds and not result.passed else [],
            "record": (Path(result.record_path).name if result.record_path else
                       previous_videos.get(video["video_id"], {}).get("record") if video["video_id"] in old_scripts else None),
            "cost_usd": result.cost_usd,
        } for video, step, result in zip(videos, steps, scripts)],
        "cost_usd": round(plan_result.cost_usd + sum(r.cost_usd for r in scripts), 6),
    }
    words = sum(len(b["say"].split()) for v in lesson["videos"] for b in v["beats"])
    lesson["quality"] = {"videos": len(videos), "videos_passed": sum(1 for v in lesson["videos"] if v["status"] == "passed"),
                         "videos_reused": sum(1 for v in lesson["videos"] if v["reused"]),
                         "plan_passed": plan_result.passed, "beats": sum(len(v["beats"]) for v in lesson["videos"]),
                         "spoken_words": words, "estimated_minutes_at_130_wpm": round(words / 130, 1),
                         "cost_usd": lesson["cost_usd"]}
    (out / "lesson_plan.json").write_text(json.dumps(lesson, ensure_ascii=False, indent=1), encoding="utf-8")
    write_pages(lesson, out)
    return lesson


def write_pages(lesson: dict, out) -> None:
    """SCRIPT.md (every video) and scripts/<video id>.md (one readable page per video)."""
    out = Path(out)
    (out / "SCRIPT.md").write_text(render_markdown(lesson), encoding="utf-8")
    folder = out / "scripts"
    folder.mkdir(exist_ok=True)
    for video in lesson["videos"]:
        (folder / f"{video['video_id']}.md").write_text(render_video_page(lesson, video), encoding="utf-8")


def render_markdown(lesson: dict) -> str:
    q = lesson["quality"]
    independence = lesson.get("reviewer_independence")
    checker = {"same_company_temporary": " Checker: the same company, another model (kamzor jaanch, a weaker check).",
               "same_model_temporary": " Checker: the same model in a fresh call (kamzor jaanch, the weakest check)."}
    lines = [f"# Lesson plan and scripts · {lesson['course']['title']}", "",
             f"Plan: {lesson['plan_status']}" + (" (reused)" if lesson.get("plan_reused") else "")
             + f"; scripts passed: {q['videos_passed']} of {q['videos']}"
             + (f" ({q['videos_reused']} reused)" if q.get("videos_reused") else "")
             + f"; {q['beats']} beats, {q['spoken_words']} spoken words (about {q['estimated_minutes_at_130_wpm']} minutes); "
             f"estimated cost ${q['cost_usd']:.4f}." + checker.get(independence, ""), ""]
    if lesson["plan"].get("chapter_flow"):
        lines += [lesson["plan"]["chapter_flow"], ""]
    lines += ["| Video | Title | Result | Rounds | Minutes planned |", "| --- | --- | --- | --- | --- |"]
    plans = {v["video_id"]: v for v in lesson["plan"].get("videos", [])}
    for video in lesson["videos"]:
        minutes = plans.get(video["video_id"], {}).get("estimated_minutes", "")
        lines.append(f"| {video['video_id']} | {video['title']} | {video['status']}" + (" (reused)" if video.get("reused") else "")
                     + f" | {video['rounds']} | {minutes} |")
    lines.append("")
    for video in lesson["videos"]:
        lines += video_lines(lesson, video, level=2)
    return "\n".join(lines)


def render_video_page(lesson: dict, video: dict) -> str:
    """One video's script as its own readable page."""
    head = [f"# {video['title']}", "", f"{lesson['course']['title']} · {lesson['course']['subject']} · "
            f"{lesson['course']['learners']} · video {video['video_id']}", ""]
    return "\n".join(head + video_lines(lesson, video, level=2))


def video_lines(lesson: dict, video: dict, *, level: int) -> list:
    types = ct.load()
    h = "#" * level
    p = {v["video_id"]: v for v in lesson["plan"].get("videos", [])}.get(video["video_id"], {})
    lines = [f"{h} {video['video_id']} · {video['title']} · {video['status']} after {video['rounds']} round(s)"
             + (" · reused" if video.get("reused") else ""), "",
             f"Goal: {p.get('goal', '')}", f"Hook: {p.get('opening_hook', '')}",
             f"Story or analogy: {p.get('story_or_analogy', '') or '(none)'}", ""]
    if video["last_problems"]:
        lines += ["Open problems:", ""] + [f"- {x}" for x in video["last_problems"][:15]] + [""]
    kinds = {cp["part_id"]: cp["type"] for cp in video.get("card_parts") or []}
    frames = {part["part_id"]: part["frame"] for part in video.get("parts") or []}
    current = None
    for beat in video["beats"]:
        pid = beat.get("part_id") or ""
        if pid != current and pid:
            kind = kinds.get(pid, "")
            lines.append(f"{h}# Part {pid}" + (f" · {kind}" if kind else ""))
            frame = frames.get(pid) or {}
            if frame:
                lines.append("_frame: " + " · ".join(f"{k}: {frame.get(k, '')}" for k in FRAME) + "_")
            lines.append("")
        current = pid
        step = beat.get("step") or 0
        pattern = types.pattern(kinds.get(pid, "")) if pid else ()
        label = f" · step {step}: {pattern[step - 1]}" if pid and 1 <= step <= len(pattern) else ""
        lines.append(f"**{beat['beat_id']} · {beat['purpose']}{label}** — {beat['say']}")
        if beat.get("voice") and beat["voice"] != beat["say"]:
            lines.append(f"  _voice: {beat['voice']}_")
        lines.append(f"  _screen: {beat['on_screen']}_")
        lines.append("")
    return lines
