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
naksha) and they still pass today's code checks; every other script with beats continues from its last answer (round 0
of the runner checks it with today's checks; the maker then patches only today's problems, Task 045d job B2).

Time and prerequisites (Navin, 23 October 2026; S2-01, S2-02, S2-03): narration is 6-8 minutes per book page.
Every teachable item has an equal share of its page; a concept's budget is the sum of its items' shares, and a
video's budget the sum of its concepts' (a very dense video may go up to 25% over with ``length_note``). The plan
starts with one 5-8 minute "pehle yeh jaan lo" video (``kind`` "prerequisites", video_id "v0") that teaches every
prerequisite of the map (ids "pre1", "pre2" ... in the map's order); a topic video reminds of them in at most two
beats. Every book item stays in must_cover and every teacher question answered from the book must be answered;
outside answers are optional, the time is won by cutting repetition and side-tracks.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import cards
from . import content_types as ct
from . import engines
from . import explanations
from . import hinglish
from . import naksha as naksha_module
from . import shots
from . import soul
from .common import SEVERITY, S, arr as _arr, checklist_text as _checklist_text, fmt as _fmt, obj as _obj, review_problems
from .runner import NOTES_SCHEMA, Step, merge_notes
from .understanding import DEFAULT_OUTPUT_TOKENS, Course, chapter_id, money

SECTION = "lesson"
PLAN_VERSION = "lesson-plan/4"
SCRIPT_VERSION = "lesson-script/5"
PLAN_SCHEMA_ID = "bie.brain.lesson-plan/3"
SCRIPT_SCHEMA_ID = "bie.brain.lesson-script/3"
PURPOSES = ["hook", "prerequisite", "explain", "example", "analogy", "story", "compare", "process_walkthrough",
            "misconception", "exam_tip", "question_to_student", "recap", "transition"]
DEVANAGARI = re.compile(r"[ऀ-ॿ]")
DEVANAGARI_DIGIT = re.compile(r"[०-९]")
SENTENCE_END = re.compile(r"[।?!.]+")
LONGEST_SENTENCE = 40        # words; Navin's style is short spoken sentences (S2-04)
FRAME = ("process", "how", "when", "conditions", "atmosphere")
CONDITIONAL_STEP = re.compile(r"\bwhen there is one\b")   # "a formula built term by term when there is one": only if there is one
MINUTES_PER_PAGE = (6.0, 8.0)        # S2-01, Navin 23 October 2026
DENSE_ALLOWANCE = 1.25               # a very dense video, with the reason in length_note
PREREQUISITE_MINUTES = (5.0, 8.0)    # the "pehle yeh jaan lo" video
PREREQUISITE_VIDEO = "prerequisites"
WORDS_PER_MINUTE = 130
TIME_TOLERANCE = 0.03        # 130 words a minute is an estimate: a script up to 3% over its upper bound is within it (Task 045d, job B)
SCRIPT_FLOOR = 0.85                  # a script may run up to 15% under its range (must_cover keeps the content); never over
MAX_REMINDER_BEATS = 2
MIN_TOPIC_MINUTES = 3.0               # a topic video's highest budget: a hook, the teaching and a recap need room               # prerequisite reminders in a topic video (S2-03)
# The frame questions a type cannot answer with "n/a" (S3-01 asks all five of every topic).
FRAME_NEEDS = {"process": ("process", "how", "when", "conditions"), "timeline": ("when", "conditions", "atmosphere"),
               "cause_effect": ("how", "conditions"), "structure": ("how",), "figure": ("how",)}

PLAN_SCHEMA = _obj({
    "notes": NOTES_SCHEMA,
    "videos": _arr(_obj({
        "video_id": S,
        "title": S,
        "goal": S,
        "kind": {"type": "string", "enum": [PREREQUISITE_VIDEO, "topic"]},
        "concept_ids": _arr(S),
        "prerequisites_taught": _arr(S),
        "opening_hook": S,
        "story_or_analogy": S,
        "estimated_minutes": {"type": "integer"},
        "length_note": S,
        "why_this_unit": S,
    })),
    "chapter_flow": S,
})
FRAME_SCHEMA = _obj({key: S for key in FRAME})
PART_SCHEMA = _obj({"part_id": S, "frame": FRAME_SCHEMA,
                    "skipped_steps": _arr(_obj({"step": {"type": "integer"}, "why": S}))})
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
    return dict(previous, notes=merge_notes(previous.get("notes"), patch.get("notes")), beats=beats, parts=parts)


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
- videos: in teaching order. First, when the source lists prerequisites, the "pehle yeh jaan lo" video: video_id "v0", kind
  "prerequisites", concept_ids [], prerequisites_taught = every prerequisite name exactly as given, estimated_minutes 5-8. Then the
  topic videos "v1", "v2" ...: kind "topic", prerequisites_taught [] (a topic video only reminds of a prerequisite, in at most 2 beats).
  title in the learner language; goal = what the student will understand after it; concept_ids = the concept ids taught in it, in
  order (every concept in some topic video); opening_hook = a real-life question, puzzle or surprise that opens it; story_or_analogy =
  the story or analogy that genuinely helps, or "" if none fits; estimated_minutes = within the video's narration budget: the sum of
  its concepts' minutes in the source (6-8 minutes per book page, S2-01); length_note = "" or, only for a very dense video, why it needs
  up to 25% more; why_this_unit = why these concepts belong together. Group concepts so that every topic video gets at least 3
  minutes (its hook, teaching and recap need room). All videos together stay within the chapter's minutes. A classification concept
  (a family: the types of a tissue, the kinds of a rock) is taught through the family pattern (the overview tree, every member in
  the same slots, the comparison, a memory trick), so keep a family and its members in one video where the time allows.
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
  "n/a: " and the reason only where a question truly does not apply to that part. skipped_steps = the teaching-pattern steps of this
  part you leave out because there is nothing real to say for them, each with the reason ([] when every step is done); at most half
  of a pattern, never a step that has something real; BIE's code records the reason.
- beats: the whole video in order. beat_id "b1", "b2" ...; part_id = the card part this beat teaches ("" for the opening hook, a
  prerequisite taught first, a transition or the final recap); step = the number of the teaching-pattern step of that part's content type
  that this beat performs (see the content types above; 0 when part_id is "" and for an exam-question part, whose type is "none");
  the steps of a part's pattern appear in order, except the ones skipped with a reason; a classification part follows the family
  pattern: the overview tree first, then every member in the same slots (layer and shape → why it is named so → its special feature
  → its function with its cause → where it is found, by a zoom from the organ → its consequence), then the comparison, then a memory
  trick; one recap per part and one closing recap for the video, never two recaps of the same thing;
  purpose (hook, prerequisite, explain, example, analogy, story, compare, process_walkthrough, misconception, exam_tip,
  question_to_student, recap, transition); say = the exact spoken words, one to four complete spoken sentences in Navin's Hinglish
  (S2-04), the way a teacher speaks to one student, never clipped note-style lines ("Irregular walls. Kaisi? Irregular." is a teacher's
  beat; "Location: kidney tubules, glandular ducts." is a note):
  mixed script: Hindi words in Devanagari, English words (above all the book's technical terms, spelled as the book spells them) in
  Roman, as in "आज हम tissue के बारे में पढ़ेंगे"; brackets only after a genuinely difficult Hindi word (see "Brackets" below; the
  screen shows the bracket and the voice says "सतह, यानी surface"); never write an English term in Devanagari or a Hindi word in Roman;
  numbers as digits; addressed to one student; covers_item_ids = the item ids this beat really explains; answers = the teacher question
  ids this beat really answers; on_screen = what the student should see while hearing it (for the director); basis = book, outside or
  mixed.
Opening the book (S2-07; BIE is the link between the learner and the book, like a teacher, never a reader of the line): every new
topic (every concept and every prerequisite) opens with a question about something the learner can see, then the name. After any
book line, the beat carries at least one of: the term opened ("yaani" + its plain meaning + one everyday image), the why from a need or
a problem, or an example or place by a zoom from the organ. The source gives every item's unpack from Section 1 (its terms, why chain,
example, consequence, visual verb) and the locked explanations: speak them, in your own teacher's words, at the depth of the level
profile below. BIE's code sends back a beat whose English words are the book's and that opens nothing ("dohraav pakad"), a clipped
sentence without a verb, a topic that opens without a question, and a second recap of the same thing.
Real-world application (S2-08; Navin, 27 October 2026: "economic concepts ko real world mein apply karke samjhao"): for an economics
definition, cause_effect or process item the source gives the real_world_example Section 1 chose (place, actors, goods, numbers before
→ after, the steps with their mechanism links, the naming sentence, the real-life link). Run that example FIRST, in beats that cover
the item and carry its numbers as digits ("dukaan mein chini ke 3 packet, ₹50 ka ek; kal 2 khareedar, aaj 12"), walking the mechanism
step by step (purpose story or example); only then the beat that names the term ("isliye ise demand-pull inflation kehte hain"), then
the book's definition, then the real-life link. The opening question of such a topic asks about the situation, not the term. BIE's
code sends back a script whose naming beat comes before the example beats, or whose example beats carry none of the numbers.
Time (S2-01): the source gives this video's narration time; BIE's code counts the spoken words (130 a minute) and the script must stay
within it. Win the time by cutting repetition and side-tracks, never book content: every item in must_cover is taught and every
teacher question whose basis is "book" is answered; questions answered from outside the book are used only where they help and the
time allows.
Prerequisites (S2-03): in a topic video they were already taught in the prerequisite video; remind of one in at most 2 beats (purpose
"prerequisite"). In the prerequisite video (card parts "pre1", "pre2" ...) teach each prerequisite simply, with an everyday example, in
the order given: part_id = the prerequisite id, step 0, covers_item_ids = the prerequisite ids the beat teaches, answers [].
A beat introduces at most a few new items: BIE's code measures the load of every beat (0.4 per new item plus 1 per 50 spoken words, at
most 1.8), so a beat holds at most about 70 spoken words with one new item, 50 with two and 30 with three; split longer beats. Reply
with the JSON object only."""

REVIEW_ROLE = """You are BIE's independent reviewer for the lesson section. Another AI wrote the work below from BIE's task card. You check
it as Navin would: is this how the best teacher would teach it?"""

REVIEW_HOW = """You also get the maker's notes. Report every problem with where it is (video, part or beat id), what is wrong, the fix and a
severity ("blocking" or "minor", see R-01): an item or teacher question not really covered (even if claimed), a part whose frame is
empty or wrong, a teaching-pattern step that is only named and not done, a prerequisite named but not taught, a jump a student cannot
follow, an analogy that does not fit, a fact wrong at this level, language that is not natural spoken Hinglish, beats that read out
lists. Precision beyond the level of a standard textbook for these learners is minor.
verdict is "pass" when nothing is blocking. Fill your own brief notes first. Reply with the JSON object only."""


SCRIPT_REVIEW_HOW = """You also get the maker's notes. Report every problem with where it is (part or beat id), what is wrong, the fix and a
severity ("blocking" or "minor", see R-01). What this script must contain (S2-01, S2-02; the same rules BIE's code checks):
- every item in card.coverage.must_cover really taught (not only named), and every teacher question whose basis is "book" really
  answered (even if claimed). A teacher question whose basis is "outside" is optional: the maker uses it only where it helps and the
  time allows, so leaving it out is never blocking; report it as minor only when leaving it out leaves a gap a student cannot cross.
- the universal frame of every part and every teaching-pattern step really done, not only named (a step skipped with a reason in
  skipped_steps is allowed when the reason is real).
- every book line opened, not read out (S2-07): the term's plain meaning with an everyday image, the why from a need, an example or the
  place; a beat that only restates the book's sentence in Hinglish is blocking; a family (classification) part gives every member the
  same slots (layer and shape, why named, special feature, function with its cause, where found by a zoom, consequence); every new
  topic opens with a question about something visible; complete spoken sentences; the depth follows the level profile below.
- for an economics concept (S2-08): the item's real-world example from Section 1 runs before the term is named, with its numbers, and
  is economically correct (the mechanism it runs is the concept's, the numbers move the way the concept says) at the learner's level
  (UPSC: the real Indian link only from the book or a dated source); a wrong mechanism or a wrong number movement is blocking.
Length (S2-01): BIE's code counts the spoken words (130 a minute) and checks the video's narration time; the review message gives the
measured minutes. Never count words or judge the length yourself. The script must stay within its time, so when you ask for something
to be added, say what may be cut (repetition, side-tracks, outside material), never book content.
Blocking: a book item or book-answered question not really covered, a fact wrong at this level, a frame or pattern step missing
without a reason, a book line only restated, a family member without its slots, a prerequisite named but not taught, a jump a student
cannot follow, language that is not natural spoken Hinglish, beats that read out lists. Minor: precision beyond a standard textbook for
these learners, an analogy that could fit better, an optional outside question, a memory trick that could be better.
verdict is "pass" when nothing is blocking. Fill your own brief notes first. Reply with the JSON object only."""

SCRIPT_TIME_HINT = (" BIE's code measured this script at {spoken} spoken minutes; the video's narration time is {low}-{high} minutes "
                    "(S2-01). Stay within it: pay for every addition with a cut of repetition or side-tracks in the same patch.")
SCRIPT_KEEP_HINT = (" Never remove beats {beats}: each is the only beat of a teaching-pattern step (recaps too); shorten them "
                    "instead.")
SCRIPT_WORDING_HINT = (" For a W-01 problem rewrite only that beat's sentence so it teaches the fact itself, as a teacher would (no "
                       "'book ke anusar', 'kitaab kehti hai', 'book says', 'page par', 'NCERT'); keep its meaning, its items and its "
                       "length; change no other beat.")


def sole_step_beats(beats) -> list:
    """Beat ids that are the only beat of their part's teaching-pattern step: removing one drops a required step (job 3,
    v9: two patches cut recap beats to save time and the script failed for the missing steps)."""
    by_step = {}
    for beat in beats:
        if beat.get("part_id") and beat.get("step"):
            by_step.setdefault((beat["part_id"], beat["step"]), []).append(beat["beat_id"])
    return [ids[0] for ids in by_step.values() if len(ids) == 1]


def question_ids(item: dict):
    return [f"{item['item_id']}#q{n}" for n in range(1, len(item.get("teacher_understanding") or []) + 1)]


def _concepts(chapter):
    return {c["concept_id"]: c for c in (chapter.get("map") or {}).get("concepts", [])}


def chapter_naksha(chapter: dict) -> dict:
    """The naksha of a chapter map (built again for maps made before Task 045, whose types are converted)."""
    return naksha_module.build(chapter)


def prerequisites_of(chapter) -> list:
    """[(prerequisite id, prerequisite)] in the map's order: "pre1", "pre2" ..."""
    return [(f"pre{n}", p) for n, p in enumerate((chapter.get("map") or {}).get("prerequisites_to_teach") or [], 1)]


def is_prerequisite_video(video: dict) -> bool:
    return video.get("kind") == PREREQUISITE_VIDEO


def book_pages(chapter) -> int:
    """The pages that have something to teach (S2-01 counts these)."""
    return len({item["page"] for item in chapter["items"].values() if item.get("teachable")})


def concept_pages(chapter) -> dict:
    """{concept id: page equivalents}: every teachable item has an equal share of its page, split between the concepts
    it belongs to; a concept's pages are the sum of its items' shares (all concepts together: the book pages)."""
    items, per_page, owners = chapter["items"], Counter(), defaultdict(set)
    for item in items.values():
        if item.get("teachable"):
            per_page[item["page"]] += 1
    for cid, concept in _concepts(chapter).items():
        for iid in concept.get("item_ids") or []:
            if items.get(iid, {}).get("teachable"):
                owners[iid].add(cid)
    out = defaultdict(float)
    for iid, cids in owners.items():
        for cid in cids:
            out[cid] += 1 / per_page[items[iid]["page"]] / len(cids)
    return dict(out)


def video_budget(chapter, videos, video, pages=None) -> tuple:
    """(lowest, highest) narration minutes of a video (S2-01): 5-8 for the prerequisite video; for a topic video 6-8 per
    book page of its items (a concept in two videos is shared), the highest x1.25 when the plan gives a length_note."""
    if is_prerequisite_video(video):
        return PREREQUISITE_MINUTES
    pages = pages if pages is not None else concept_pages(chapter)
    count = Counter(cid for v in videos for cid in v.get("concept_ids") or [])
    share = sum(pages.get(cid, 0.0) / max(1, count[cid]) for cid in video.get("concept_ids") or [])
    low, high = share * MINUTES_PER_PAGE[0], share * MINUTES_PER_PAGE[1]
    if (video.get("length_note") or "").strip():
        high *= DENSE_ALLOWANCE
    return round(low, 1), round(high, 1)


def chapter_budget(chapter, videos) -> tuple:
    """(lowest, highest) minutes of the topic videos together (S2-01: 6-8 per book page); the prerequisite video's 5-8
    minutes come on top, so a short chapter can always meet the rule."""
    total = book_pages(chapter)
    pages = concept_pages(chapter)
    extra = sum(video_budget(chapter, videos, v, pages)[1] * (1 - 1 / DENSE_ALLOWANCE) for v in videos
                if not is_prerequisite_video(v) and (v.get("length_note") or "").strip())
    return round(total * MINUTES_PER_PAGE[0], 1), round(total * MINUTES_PER_PAGE[1] + extra, 1)


def time_problems(value, chapter) -> list:
    """S2-01 and S2-03 in the plan: one prerequisite video first, every video within its budget, the chapter in its time."""
    problems = []
    videos = value.get("videos") or []
    prerequisites = prerequisites_of(chapter)
    first = [v for v in videos if is_prerequisite_video(v)]
    if prerequisites and len(first) != 1:
        problems.append(f"the plan needs exactly one prerequisite video (kind \"{PREREQUISITE_VIDEO}\", the \"pehle yeh jaan lo\" "
                        f"video) that teaches the chapter's {len(prerequisites)} prerequisites; it has {len(first)} (S2-01, S2-03)")
    elif first and not prerequisites:
        problems.append("the chapter map lists no prerequisites, so the plan has no prerequisite video (S2-03)")
    elif first and videos[0] is not first[0]:
        problems.append(f"the prerequisite video {first[0]['video_id']} comes first (S2-01)")
    names = {p["name"].strip().lower(): p["name"] for _, p in prerequisites}
    pages = concept_pages(chapter)
    for video in videos:
        low, high = video_budget(chapter, videos, video, pages)
        if is_prerequisite_video(video):
            if video.get("concept_ids"):
                problems.append(f"video {video['video_id']}: the prerequisite video teaches only the prerequisites; its concept_ids "
                                "are []")
            taught = {n.strip().lower() for n in video.get("prerequisites_taught") or []}
            missing = [names[n] for n in names if n not in taught]
            unknown = sorted(taught - set(names))
            if missing:
                problems.append(f"video {video['video_id']}: prerequisites not taught: {missing[:10]} (use the exact names; S2-03)")
            if unknown:
                problems.append(f"video {video['video_id']}: {unknown[:5]} are not prerequisites of the chapter map")
        elif video.get("prerequisites_taught"):
            problems.append(f"video {video['video_id']}: prerequisites are taught in the prerequisite video, so prerequisites_taught "
                            "is []; a topic video reminds of them in at most 2 beats (S2-03)")
        elif high < MIN_TOPIC_MINUTES and len([v for v in videos if not is_prerequisite_video(v)]) > 1:
            problems.append(f"video {video['video_id']}: its concepts get only {low}-{high} minutes; a topic video needs at least "
                            f"{MIN_TOPIC_MINUTES:g} minutes for its hook, teaching and recap, so merge it with the video before or "
                            "after (S2-01)")
        minutes = video.get("estimated_minutes", 0)
        if minutes < math.floor(low) or minutes > math.ceil(high):
            why = ("the prerequisite video is 5-8 minutes" if is_prerequisite_video(video) else
                   "6-8 minutes per book page of its items, up to 25% more only with a length_note")
            problems.append(f"video {video['video_id']}: {minutes} minutes is outside its narration budget of {low}-{high} "
                            f"minutes ({why}; S2-01)")
    topics = [v for v in videos if not is_prerequisite_video(v)]
    if topics:
        low, high = chapter_budget(chapter, videos)
        total = sum(v.get("estimated_minutes", 0) for v in topics)
        if total < math.floor(low) or total > math.ceil(high):
            problems.append(f"the topic videos add up to {total} minutes; {book_pages(chapter)} book pages get {low}-{high} "
                            "minutes (6-8 per page; the prerequisite video's 5-8 minutes come on top; S2-01)")
    return problems


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
        if not video["concept_ids"] and not is_prerequisite_video(video):
            problems.append(f"video {video['video_id']}: teaches no concept")
    for cid in sorted(set(concepts) - taught):
        problems.append(f"concept {cid} ({concepts[cid]['name']}) is in no video (S2-01)")
    problems += engines.plan_checks(value.get("videos") or [], list(concepts.values()),
                                    (chapter.get("map") or {}).get("prerequisites_to_teach", []))[0]
    problems += time_problems(value, chapter)
    if not value.get("videos"):
        problems.append("the plan has no videos")
    return problems


def book_questions(chapter, questions) -> list:
    """The teacher questions answered from the book: these must be answered in the script (S2-02)."""
    out = []
    for qid in questions:
        iid, n = qid.rsplit("#q", 1)
        qa = (chapter["items"].get(iid, {}).get("teacher_understanding") or [])[int(n) - 1:int(n)]
        if qa and qa[0].get("basis") == "book":
            out.append(qid)
    return out


def video_scope(chapter, video):
    """The items and teacher questions a video must cover (the prerequisite video: its prerequisites, no questions)."""
    if is_prerequisite_video(video):
        return [{"item_id": pid, "page": 0, "teachable": True, "kind": "prerequisite"} for pid, _ in prerequisites_of(chapter)], []
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

def _prefix(course, rulebook, task, schema_id, schema, role, how, *, review=False, version=3):
    if review:
        return cards.build_prefix(section=SECTION, task=task, version=version, schema_id=schema_id, schema=schema, role=role,
                                  how=how, rulebook=rulebook, course=course, patterns=True, review=True,
                                  checklist=_checklist_text(rulebook, SECTION))
    return cards.build_prefix(section=SECTION, task=task, version=version, schema_id=schema_id, schema=schema,
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
    pages = concept_pages(chapter)
    total = book_pages(chapter)
    budget = " | ".join(f"{cid} {pages.get(cid, 0) * MINUTES_PER_PAGE[0]:.1f}-{pages.get(cid, 0) * MINUTES_PER_PAGE[1]:.1f}"
                        for cid in _concepts(chapter))
    time = (f"Narration time (S2-01): 6-8 minutes per book page; this chapter has {total} book pages, so the topic videos together "
            f"{total * MINUTES_PER_PAGE[0]:.0f}-{total * MINUTES_PER_PAGE[1]:.0f} minutes, plus the 5-8 minute prerequisite video. "
            f"Minutes per concept (a topic video's budget is the sum of its concepts'):\n{budget}")
    return (f"Chapter summary: {m.get('chapter_summary', '')}\n\nHow the concepts link (from link to):\n{links or '(none)'}\n\n"
            f"Prerequisites to teach (name · needed for · basis · why):\n{prereq or '(none)'}\n\n"
            f"BIE's teaching order: {', '.join(naksha['order'])}\n\nExam focus:\n{focus or '(none)'}\n\n{time}")


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
    order = [v["video_id"] for v in plan["videos"]]
    position = order.index(video["video_id"])
    around = dict(before=plan["videos"][position - 1]["title"] if position else "",
                  after=plan["videos"][position + 1]["title"] if position + 1 < len(order) else "")
    if is_prerequisite_video(video):
        prerequisites = prerequisites_of(chapter)
        parts = [cards.part(pid, [pid], ct.NONE, f"prerequisite: {naksha_module.short(p['name'], 80)}: explain it simply with an "
                            "everyday example", types=types) for pid, p in prerequisites]
        needed = list(dict.fromkeys(c for _, p in prerequisites for c in p.get("needed_for") or [] if c in index.concepts))
        card = cards.make(
            prefix=prefix, chapter_id=chapter_id(course),
            unit={"unit_id": video["video_id"], "title": video["title"],
                  "pages": sorted({row[2] for row in naksha["items"]}) or [1]},
            parts=parts, rules=_rules(rulebook), mode="full", max_output_tokens=max_output_tokens,
            must_cover=[pid for pid, _ in prerequisites], claim_field="beats[].covers_item_ids", may_skip=[],
            map_slice=[index.concept_row(cid) for cid in needed], block_ids=[], page_images=[], **around)
        return cards.require_valid(card, prefix=prefix, rulebook=rulebook, types=types,
                                   known_ids=_known(chapter, index) | {pid for pid, _ in prerequisites})
    items, _ = video_scope(chapter, video)
    parts = script_parts(chapter, naksha, video, types)
    must = [i for p in parts for i in p["item_ids"]]
    skip = [{"item_id": i["item_id"], "reason": "not teachable (heading or container)"} for i in items if not i.get("teachable")]
    card = cards.make(
        prefix=prefix, chapter_id=chapter_id(course),
        unit={"unit_id": video["video_id"], "title": video["title"], "pages": sorted({i["page"] for i in items})},
        parts=parts or [cards.part("none", [video["concept_ids"][0]], "facts_numbers", "no teachable items", types=types)],
        rules=_rules(rulebook), mode="full", max_output_tokens=max_output_tokens, must_cover=must,
        claim_field="beats[].covers_item_ids", may_skip=skip, map_slice=naksha_module.slice_rows(naksha, must, index=index),
        block_ids=[b for i in items for b in i.get("block_ids") or []], page_images=[], **around)
    return cards.require_valid(card, prefix=prefix, rulebook=rulebook, known_ids=_known(chapter, index), types=types)


def _script_source(chapter, video, budget=None) -> str:
    items, _ = video_scope(chapter, video)
    low, high = budget or (None, None)
    lines = [f"Video {video['video_id']}: {video['title']}", f"Goal: {video['goal']}", f"Opening hook: {video['opening_hook']}",
             f"Story or analogy: {video['story_or_analogy'] or '(none)'}", f"Planned minutes: {video['estimated_minutes']}"]
    if budget:
        lines.append(f"Narration time (S2-01): {low}-{high} minutes, about {round(low * WORDS_PER_MINUTE)}-"
                     f"{round(high * WORDS_PER_MINUTE)} spoken words (BIE counts {WORDS_PER_MINUTE} words a minute)")
    concepts = _concepts(chapter)
    if is_prerequisite_video(video):
        lines.append("\nPrerequisites to teach, in this order (id | name | basis | needed for | why):")
        for pid, p in prerequisites_of(chapter):
            needed = ", ".join(concepts.get(c, {}).get("name", c) for c in p.get("needed_for") or [])
            lines.append(f"{pid} | {p['name']} | {p.get('basis', '')} | {needed} | {p.get('why_needed', '')}")
        return "\n".join(lines)
    names = [p["name"] for _, p in prerequisites_of(chapter)]
    if names:
        lines.append("Prerequisites already taught in the prerequisite video (remind of one in at most 2 beats): " + "; ".join(names))
    lines.append("Open every book line (S2-07): " + "; ".join(soul.load_teacher()["opening_steps"]) + ".")
    lines.append("\nItems (item id | page | kind | type | content), each with its teacher questions "
                 "(question id | ask | question → answer | basis) and its unpack from Section 1 (term | why | example | consequence "
                 "| visual), plus any locked explanation (Navin's verdict: speak it):")
    library = explanations.load()
    subject = (chapter.get("course") or {}).get("subject", "")
    for item in items:
        content = re.sub(r"\s+", " ", item.get("content", "")).strip()
        lines.append(f"{item['item_id']} | {item['page']} | {item['kind']} | {item.get('content_type', '')} | {content}")
        for qid, qa in zip(question_ids(item), item.get("teacher_understanding") or []):
            lines.append(f"  {qid} | {qa['ask']} | {qa['question']} → {qa['answer']} | {qa['basis']}")
        lines += soul.unpack_lines(item.get("unpack"))
        locked = library.source_lines(content, subject=subject)
        if locked:
            lines.append(locked)
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
            technical = hinglish.technical_words(b["say"])
            if technical:
                pairs = ", ".join(f"{word} → {english}" for word, english in technical[:5])
                problems.append(f"beat {b['beat_id']}: textbook Hindi for the book's own terms ({pairs}); say the book's English term in "
                                "Roman, a bracket does not rescue it (S2-04)")
            hard = [w for w in hinglish.difficult_words(b["say"]) if not any(w == t for t, _ in technical)]
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
    skip_problems, skipped = soul.skipped_step_problems(value.get("parts") or [], card["parts"], types)
    problems += skip_problems
    observed["skipped_steps"] = skipped
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
        for step in skipped.get(pid, {}):
            if step in done:
                problems.append(f"part {pid}: step {step} is listed in skipped_steps but beats perform it; skip it or do it (S2-07)")
        missing = [n for n in range(1, len(pattern) + 1)
                   if n not in done and n not in skipped.get(pid, {}) and not CONDITIONAL_STEP.search(pattern[n - 1])]
        if missing:
            names = "; ".join(f"{n}) {pattern[n - 1]}" for n in missing)
            problems.append(f"part {pid} ({part['type']}): teaching-pattern steps not taught: {names}")
        if done != sorted(done):
            observed["pattern_order"].append(pid)
    return problems, observed


def chapter_family(chapter: dict) -> str:
    return shots.subject_family((chapter.get("course") or {}).get("subject", ""))


def check_script(value, chapter, video, language, card=None, budget=None):
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
    missing_q = [q for q in book_questions(chapter, questions) if q not in answered]
    if missing_q:
        problems.append(f"{len(missing_q)} teacher questions answered from the book are answered by no beat (S2-02): "
                        f"{', '.join(missing_q[:40])}")
    problems += spoken_problems(beats, language)
    problems += length_problems(beats, video, budget)
    problems += soul.restatement_problems(beats, chapter["items"])
    problems += soul.clipped_problems(beats)
    problems += soul.recap_problems(beats)
    problems += soul.wording_problems(beats)
    if len(beats) < 3:
        problems.append("a video needs more than a couple of beats")
    if card is not None:
        problems += soul.opening_problems(beats, card["parts"])
        problems += soul.example_order_problems(beats, chapter["items"], card["parts"], family=chapter_family(chapter), types=ct.load())
        problems += frame_problems(value, card)[0]
        problems += engines.script_checks(beats, card["coverage"]["must_cover"], planned_minutes=video.get("estimated_minutes"),
                                          minutes_range=budget)[0]
    return problems


def spoken_minutes(beats) -> float:
    return round(sum(len(b.get("say", "").split()) for b in beats) / WORDS_PER_MINUTE, 1)


def length_problems(beats, video, budget) -> list:
    """S2-01 and S2-03 in a script: within its narration time, and at most 2 prerequisite reminders in a topic video."""
    problems = []
    if budget:
        low, high = budget
        spoken = spoken_minutes(beats)
        if spoken > round(high * (1 + TIME_TOLERANCE), 1):
            problems.append(f"the script speaks about {spoken} minutes; this video's narration time is {low}-{high} minutes "
                            f"(S2-01): cut repetition and side-tracks, never book content")
        elif spoken < round(low * SCRIPT_FLOOR, 1):
            problems.append(f"the script speaks only about {spoken} minutes; this video's narration time is {low}-{high} minutes "
                            "(S2-01): explain the book's items fully")
    if not is_prerequisite_video(video):
        reminders = [b["beat_id"] for b in beats if b.get("purpose") == "prerequisite"]
        if len(reminders) > MAX_REMINDER_BEATS:
            problems.append(f"beats {', '.join(reminders[:10])} are prerequisite beats; a topic video reminds of prerequisites in at "
                            f"most {MAX_REMINDER_BEATS} beats, they are taught in the prerequisite video (S2-03)")
    return problems


# ---------------------------------------------------------------- steps

def plan_step(course: Course, chapter, *, rulebook, max_rounds=3, naksha=None, max_output_tokens=DEFAULT_OUTPUT_TOKENS) -> Step:
    naksha = naksha or chapter_naksha(chapter)
    prefix = _prefix(course, rulebook, "plan_videos", PLAN_SCHEMA_ID, PLAN_SCHEMA, PLAN_ROLE,
                     PLAN_HOW + "\n\n" + course.profile().prefix_text())
    review_prefix = _prefix(course, rulebook, "plan_videos", "bie.brain.lesson-plan-review/2", REVIEW_SCHEMA, REVIEW_ROLE,
                            REVIEW_HOW, review=True, version=2)
    card = plan_card(course, chapter, naksha, rulebook=rulebook, prefix=prefix, max_output_tokens=max_output_tokens)
    source = _plan_source(chapter, naksha)
    user = cards.user_message(card, source, (), "Answer the card with the lesson plan JSON.")

    def review_user(value):
        return cards.user_message(card, source + "\n\nThe lesson plan to review (JSON):\n" + cards.compact(value),
                                  (), "Review the plan; reply with the review JSON.")

    observe = lambda value: engines.plan_checks(value.get("videos") or [], [], (chapter.get("map") or {}).get(
        "prerequisites_to_teach", []))[1]
    return Step(section=SECTION, unit="plan", instructions_version=PLAN_VERSION, system=prefix.text, user=user, schema=PLAN_SCHEMA,
                check=lambda value: check_plan(value, chapter), review_system=review_prefix.text, review_user=review_user,
                review_schema=REVIEW_SCHEMA, review_problems=review_problems, max_rounds=max_rounds, card=card, observe=observe)


def script_prefixes(course, rulebook):
    profile = course.profile()
    how = "\n\n".join([SCRIPT_HOW, profile.prefix_text(), soul.teacher_text(), hinglish.prefix_text()])
    return (_prefix(course, rulebook, "write_script", SCRIPT_SCHEMA_ID, SCRIPT_SCHEMA, SCRIPT_ROLE, how),
            _prefix(course, rulebook, "write_script", "bie.brain.lesson-script-review/4", REVIEW_SCHEMA, REVIEW_ROLE,
                    SCRIPT_REVIEW_HOW + "\n\n" + profile.prefix_text(), review=True, version=4))


def script_step(course: Course, chapter, plan, video, *, rulebook, max_rounds=3, naksha=None, prefixes=None,
                max_output_tokens=DEFAULT_OUTPUT_TOKENS, start: dict | None = None) -> Step:
    naksha = naksha or chapter_naksha(chapter)
    prefix, review_prefix = prefixes or script_prefixes(course, rulebook)
    card = script_card(course, chapter, naksha, plan, video, rulebook=rulebook, prefix=prefix, max_output_tokens=max_output_tokens)
    budget = video_budget(chapter, plan["videos"], video)
    source = _script_source(chapter, video, budget)
    user = cards.user_message(card, source, (), "Answer the card with the teacher script JSON.")

    def review_user(value):
        measured = (f"\n\nBIE's code measured: {spoken_minutes(value.get('beats') or [])} spoken minutes; narration time "
                    f"{budget[0]}-{budget[1]} minutes (S2-01, already checked by code)." if budget else "")
        return cards.user_message(card, source + measured + "\n\nThe teacher script to review (JSON):\n" + cards.compact(value),
                                  (), "Review the script; reply with the review JSON.")

    def patch_hint(value):
        low, high = budget or (None, None)
        beats = value.get("beats") or []
        keep = sole_step_beats(beats)
        return (SCRIPT_PATCH_HINT
                + (SCRIPT_TIME_HINT.format(spoken=spoken_minutes(beats), low=low, high=high) if budget else "")
                + (SCRIPT_KEEP_HINT.format(beats=", ".join(keep[:60])) if keep else "")
                + (SCRIPT_WORDING_HINT if soul.wording_hits(beats) else ""))

    def observe(value):
        found = frame_problems(value, card)[1]
        found.update(engines.script_checks(value.get("beats") or [], card["coverage"]["must_cover"],
                                           planned_minutes=video.get("estimated_minutes"), minutes_range=budget)[1])
        found["dohraav"] = soul.dohraav_share(value.get("beats") or [], chapter["items"])
        found["real_world"] = soul.example_order_report(value.get("beats") or [], chapter["items"], card["parts"],
                                                        family=chapter_family(chapter), types=ct.load())
        return found

    return Step(section=SECTION, unit=f"script-{video['video_id']}", instructions_version=SCRIPT_VERSION, system=prefix.text,
                user=user, schema=SCRIPT_SCHEMA,
                check=lambda value: check_script(value, chapter, video, course.language, card, budget),
                review_system=review_prefix.text, review_user=review_user, review_schema=REVIEW_SCHEMA,
                review_problems=review_problems, patch_schema=SCRIPT_PATCH_SCHEMA, apply_patch=apply_script_patch,
                patch_hint=patch_hint, max_rounds=max_rounds, card=card, observe=observe, normalize=tidy_script,
                start=start)


def tidy_script(value: dict) -> tuple:
    """(value, changes): BIE's code removes brackets after everyday Hindi words and inside fixed phrases (S2-04), so the
    maker is never sent back for them and the reviewer reads the tidy script."""
    removed, beats = [], []
    for beat in value.get("beats") or []:
        say, gone = hinglish.clean(beat.get("say", ""))
        if gone:
            removed.append({"beat_id": beat.get("beat_id"), "removed": gone})
            beat = dict(beat, say=say)
        beats.append(beat)
    return (dict(value, beats=beats), {"brackets_removed": removed}) if removed else (value, {})


def _script_value(video_entry: dict) -> dict:
    """A script as the maker wrote it, from a lesson_plan.json video (without the code-made subtitle and voice)."""
    beats = [{k: v for k, v in b.items() if k not in ("subtitle", "voice")} for b in video_entry.get("beats") or []]
    return {"notes": None, "title": video_entry.get("title", ""), "parts": video_entry.get("parts") or [], "beats": beats}


CONTINUE_LIMIT = 10        # an earlier script with at most this many problems today is finished, not written again


def close_enough(problems: list) -> bool:
    """An earlier script is worth continuing when it has few problems today and none of them means missing content (an
    item or a teacher question not covered, S2-02) or a script far too short; otherwise it is written again."""
    return len(problems) <= CONTINUE_LIMIT and not any("(S2-02)" in p or "speaks only about" in p for p in problems)


def reusable(previous: dict | None, chapter: dict, naksha: dict, course: Course, rulebook, only=None) -> tuple:
    """(plan or None, {video id: script value}, notes, {video id: script value to continue}): what an earlier lesson run
    may give this one.

    Nothing is reused when the chapter map changed (another naksha). The plan is reused when it passed and still
    passes today's checks; a script only with its plan, when it passed and still passes today's checks on today's card.
    Every other script of that plan that has beats (it failed, stopped, or passed but fails today's checks) and is close
    enough (``close_enough``) is continued: its last answer is the start of the new run, which fixes only today's problems
    instead of writing it again (job B, 24 October 2026: three of the seven scripts written again from scratch failed on
    new words of their own). A script far from passing is written again.

    ``only`` (Task 046, VM job 1: a wording patch on v3 alone): the video ids this run may work on; every other script
    with beats is kept exactly as it was, checked or not, and its entry says so (``kept``).
    """
    notes, starts = [], {}
    only = set(only or ())
    if not previous:
        return None, {}, notes, starts
    if previous.get("naksha_sha256") != naksha["sha256"]:
        return None, {}, ["the chapter map changed since the earlier run, so nothing is reused"], starts
    plan = previous.get("plan") or {}
    if previous.get("plan_status") != "passed" or not plan.get("videos"):
        return None, {}, ["the earlier plan did not pass, so the plan and the scripts run again"], starts
    problems = check_plan(plan, chapter)
    if problems:
        return None, {}, [f"the earlier plan fails today's checks ({problems[0][:120]}), so it runs again"], starts
    prefix = script_prefixes(course, rulebook)[0]
    scripts = {}
    by_id = {v["video_id"]: v for v in previous.get("videos") or []}
    for video in plan["videos"]:
        entry = by_id.get(video["video_id"])
        if not entry or not entry.get("beats"):
            continue
        card = script_card(course, chapter, naksha, plan, video, rulebook=rulebook, prefix=prefix)
        value = tidy_script(_script_value(entry))[0]
        problems = check_script(value, chapter, video, course.language, card, video_budget(chapter, plan["videos"], video))
        vid, status = video["video_id"], entry.get("status", "did not pass")
        if only and vid not in only:
            scripts[vid] = value
            notes.append(f"{vid} kept as it was (not selected for this run" + (f"; {len(problems)} problems today)" if problems else ")"))
        elif status == "passed" and not problems:
            scripts[vid] = value
        elif close_enough(problems):
            starts[vid] = value
            notes.append(f"{vid} fails today's checks ({problems[0][:120]}), so it continues from its last answer" if problems
                         else f"{vid} {status} earlier, so it continues from its last answer")
        else:
            notes.append(f"{vid} fails today's checks ({problems[0][:120]}), so it runs again")
    return plan, scripts, notes, starts


def run_lesson(chapter: dict, course: Course, runner, out_dir, *, workers: int = 4, max_rounds: int = 3,
               max_output_tokens: int = DEFAULT_OUTPUT_TOKENS, previous_lesson: dict | None = None, only=None):
    """``only``: video ids to work on in a resumed run; the other scripts are kept as they were (Task 046, VM job 1)."""
    from .runner import StepResult

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    naksha = chapter_naksha(chapter)
    book = cards.CardBook()                 # a card id is used once per run
    step = plan_step(course, chapter, rulebook=runner.rulebook, max_rounds=max_rounds, naksha=naksha,
                     max_output_tokens=max_output_tokens)
    book.add(step.card)
    old_plan, old_scripts, resume_notes, starts = reusable(previous_lesson, chapter, naksha, course, runner.rulebook, only=only)
    kept = {vid for vid in old_scripts if only and vid not in set(only)}
    if old_plan is not None:
        plan_result = StepResult(SECTION, "plan", "passed", dict(old_plan, notes=None), record_path=None)
    else:
        plan_result = runner.run(step)
    plan = plan_result.output or {"videos": []}
    videos = plan.get("videos") or [] if plan_result.passed else []
    prefixes = script_prefixes(course, runner.rulebook)
    steps = [script_step(course, chapter, plan, v, rulebook=runner.rulebook, max_rounds=max_rounds, naksha=naksha,
                         prefixes=prefixes, max_output_tokens=max_output_tokens,
                         start=starts.get(v["video_id"]) if old_plan is not None else None) for v in videos]
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
            "status": previous_videos[video["video_id"]].get("status", result.status) if video["video_id"] in kept else result.status,
            "rounds": len(result.rounds) if video["video_id"] not in old_scripts else previous_videos[video["video_id"]]["rounds"],
            "reused": video["video_id"] in old_scripts,
            "kept": video["video_id"] in kept,
            "continued": video["video_id"] in starts and video["video_id"] not in old_scripts and old_plan is not None,
            "parts": (result.output or {}).get("parts", []),
            "card_parts": [{k: p[k] for k in ("part_id", "type", "item_ids")} for p in step.card["parts"]],
            "beats": [dict(b, subtitle=hinglish.subtitle_text(b["say"]), voice=hinglish.voice_text(b["say"]))
                      for b in (result.output or {}).get("beats", [])],
            "kind": video.get("kind", "topic"),
            "budget_minutes": list(video_budget(chapter, videos, video)),
            "spoken_minutes": spoken_minutes((result.output or {}).get("beats", [])),
            "dohraav": soul.dohraav_share((result.output or {}).get("beats", []), chapter["items"]),
            "real_world": soul.example_order_report((result.output or {}).get("beats", []), chapter["items"], step.card["parts"],
                                                    family=chapter_family(chapter), types=ct.load()),
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
    judged = sum(v["dohraav"]["judged"] for v in lesson["videos"])
    lesson["quality"] = {"videos": len(videos), "videos_passed": sum(1 for v in lesson["videos"] if v["status"] == "passed"),
                         "dohraav": {"judged_beats": judged, "restating": sum(v["dohraav"]["restating"] for v in lesson["videos"]),
                                     "share": round(sum(v["dohraav"]["restating"] for v in lesson["videos"]) / judged, 3) if judged else 0.0,
                                     "opened_share": round(sum(v["dohraav"]["opened"] for v in lesson["videos"]) / judged, 3) if judged else 0.0},
                         "real_world": {"items": sum(len(v["real_world"]) for v in lesson["videos"]),
                                        "run_first": sum(1 for v in lesson["videos"] for r in v["real_world"] if r["ok"])},
                         "videos_reused": sum(1 for v in lesson["videos"] if v["reused"]),
                         "videos_continued": sum(1 for v in lesson["videos"] if v.get("continued")),
                         "plan_passed": plan_result.passed, "beats": sum(len(v["beats"]) for v in lesson["videos"]),
                         "spoken_words": words, "estimated_minutes_at_130_wpm": round(words / 130, 1),
                         "budget_minutes": {"topic_videos": list(chapter_budget(chapter, videos)) if videos else None,
                                            "prerequisite_video": list(PREREQUISITE_MINUTES), "per_page": list(MINUTES_PER_PAGE),
                                            "book_pages": book_pages(chapter)},
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
             + (f" ({q['videos_continued']} continued from an earlier run)" if q.get("videos_continued") else "")
             + f"; {q['beats']} beats, {q['spoken_words']} spoken words (about {q['estimated_minutes_at_130_wpm']} minutes); "
             f"estimated cost {money(q['cost_usd'], lesson)}." + checker.get(independence, "")
             + (f" Dohraav (beats that only restate the book): {q['dohraav']['restating']} of {q['dohraav']['judged_beats']} "
                f"({q['dohraav']['share']:.0%}); beats that open a term, a why or an example: {q['dohraav']['opened_share']:.0%}."
                if q.get("dohraav") else ""), ""]
    budget = q.get("budget_minutes") or {}
    if budget.get("topic_videos"):
        low, high = budget["topic_videos"]
        lines += [f"Narration time (S2-01): {budget['per_page'][0]:g}-{budget['per_page'][1]:g} minutes per book page, "
                  f"{budget['book_pages']} pages, topic videos {low}-{high} minutes; the prerequisite video "
                  f"{budget['prerequisite_video'][0]:g}-{budget['prerequisite_video'][1]:g} minutes on top.", ""]
    if lesson["plan"].get("chapter_flow"):
        lines += [lesson["plan"]["chapter_flow"], ""]
    lines += ["| Video | Kind | Title | Result | Rounds | Minutes planned | Budget | Spoken (130 words/min) | Dohraav |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    plans = {v["video_id"]: v for v in lesson["plan"].get("videos", [])}
    for video in lesson["videos"]:
        minutes = plans.get(video["video_id"], {}).get("estimated_minutes", "")
        lines.append(f"| {video['video_id']} | {video.get('kind', 'topic')} | {video['title']} | {video['status']}"
                     + (" (reused)" if video.get("reused") else "") + (" (continued)" if video.get("continued") else "")
                     + f" | {video['rounds']} | {minutes} | "
                     + ("{}-{}".format(*video["budget_minutes"]) if video.get("budget_minutes") else "") + " | "
                     + (f"{video['spoken_minutes']}" if video.get("spoken_minutes") is not None else "") + " | "
                     + (f"{video['dohraav']['restating']}/{video['dohraav']['judged']}" if video.get("dohraav") else "") + " |")
    lines.append("")
    rows = [(v, r) for v in lesson["videos"] for r in v.get("real_world") or []]
    if rows:
        items = {}
        lines += ["## Real-world examples (S2-08, Navin's rule of 27 October 2026)", "",
                  "Every economics concept item of these scripts: the beats that run its example (they cover the item and carry its "
                  "numbers), the beat that names the term, and today's check (the example must run first).", "",
                  "| Video | Item | Place | Example beats | Names the term | Check |", "| --- | --- | --- | --- | --- | --- |"]
        for video, r in rows:
            named = f"{r['term_beat']} ({r['term']})" if r.get("term_beat") else "(term not named by a beat)"
            check = "ok" if r["ok"] else r["problem"].split(": ", 1)[-1][:110]
            lines.append(f"| {video['video_id']} | {r['item_id']} | {r['place']} | {', '.join(r['example_beats']) or '(none)'} | {named} | {check} |")
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
             + (" · reused" if video.get("reused") else "") + (" · continued from an earlier run" if video.get("continued") else ""), "",
             (f"Kind: {'pehle yeh jaan lo (prerequisite video)' if video.get('kind') == PREREQUISITE_VIDEO else 'topic video'}"
              + (" · budget {}-{} minutes".format(*video["budget_minutes"]) if video.get("budget_minutes") else "")
              + (f" · spoken about {video['spoken_minutes']} minutes" if video.get("spoken_minutes") is not None else "")
              + (f" · length note: {p['length_note']}" if p.get("length_note") else "")),
             f"Goal: {p.get('goal', '')}", f"Hook: {p.get('opening_hook', '')}",
             f"Story or analogy: {p.get('story_or_analogy', '') or '(none)'}", ""]
    if video["last_problems"]:
        lines += ["Open problems:", ""] + [f"- {x}" for x in video["last_problems"][:15]] + [""]
    kinds = {cp["part_id"]: cp["type"] for cp in video.get("card_parts") or []}
    frames = {part["part_id"]: part["frame"] for part in video.get("parts") or []}
    skipped = {part["part_id"]: part.get("skipped_steps") or [] for part in video.get("parts") or []}
    current = None
    for beat in video["beats"]:
        pid = beat.get("part_id") or ""
        if pid != current and pid:
            kind = kinds.get(pid, "")
            lines.append(f"{h}# Part {pid}" + (f" · {kind}" if kind else ""))
            frame = frames.get(pid) or {}
            if frame:
                lines.append("_frame: " + " · ".join(f"{k}: {frame.get(k, '')}" for k in FRAME) + "_")
            if skipped.get(pid):
                lines.append("_skipped steps: " + "; ".join(f"{e['step']}: {e['why']}" for e in skipped[pid]) + "_")
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
