"""Passed outputs stay passed: today's code checks re-run on everything that passed in earlier live runs.

Navin's standing rule "seekh → BIE" (CLAUDE.md, 23 October 2026) lets Claude change BIE after every live run without
asking (new checks, instructions, code that takes work from the AI), on the condition that no change fails an output
that passed before. This module keeps that promise checkable. ``export`` turns a run's passed work into a compact set (``bie.brain.
passed-outputs/1``): every passed page's items with the page's native text blocks and the card's coverage, the
chapter map when it passed, the lesson plan and every passed script. ``check`` runs today's code checks (the same
functions the section runner uses) on such a set and returns every problem; an empty list means every earlier
passed output still passes. The sets live in ``tests/fixtures/passed_outputs/`` and a test runs them all.

These sets are BIE's own outputs kept for regression; they are not accepted examples (that needs Navin's verdict).

When Navin changes a rule, older passed work can break the new rule on purpose. Such a problem is not a regression:
``RULE_CHANGES`` names the rule, Navin's decision, the first rulebook version with it and the BIE step that upgrades
older work (never a hand edit). ``check`` leaves those problems out for sets made before the change and
``changed_rule_problems`` lists them, so they stay visible.
"""
from __future__ import annotations

import gzip
import json
import re
from pathlib import Path

from . import content_types as ct
from . import engines

SCHEMA = "bie.brain.passed-outputs/1"

VISION = "vision-2026-10-21"
RULE_CHANGES = (
    {"rule": "S1-12", "rulebook": f"{VISION}@2026-10-21.10",
     "decision": "Navin, 23 October 2026: only direct prerequisites, no chains, taught in one short video; more than 8 needs a reason",
     "upgraded_by": "bie/brain/prerequisites.py (trim_prerequisites, run before a lesson is planned)",
     "match": re.compile(r"^map: prerequisites_to_teach has \d+ prerequisites")},
    {"rule": "S1-15", "rulebook": f"{VISION}@2026-10-21.12",
     "decision": "Navin, 24 October 2026 (Task 045d): every teachable item is opened for the learner (terms with their plain meaning "
                 "and an everyday image, a why chain from a need with its basis, an example or place, a consequence)",
     "upgraded_by": "the page is read again (bie/brain/understanding.py, schema bie.brain.understand-page/3); an older page is not reused",
     "match": re.compile(r"\(S1-15\)$")},
    {"rule": "S2-07", "rulebook": f"{VISION}@2026-10-21.12",
     "decision": "Navin, 24 October 2026 (Task 045d): every book line opened, not read out: a question first, yaani with an image, "
                 "a why or an example after a book line, complete sentences, one recap per part, steps skipped only with a reason",
     "upgraded_by": "the script is written again (bie/brain/lesson.py, schema bie.brain.lesson-script/3)",
     "match": re.compile(r"\(S2-07\)$")},
    {"rule": "S2-06 (classification pattern)", "rulebook": "content_types@2026-10-24.1",
     "decision": "Navin, 24 October 2026 (Task 045d): a classification is taught as a family: the overview tree, every member in the "
                 "same slots, the members compared, a memory trick",
     "upgraded_by": "the script is written again (bie/brain/lesson.py)",
     "match": re.compile(r"^script \S+: (?:part \S+ \(classification\): teaching-pattern steps not taught"
                         r"|beat \S+: step \d+ is not a step of the classification pattern)")},
    {"rule": "W-01", "rulebook": "visual_grammar@2026-10-26.1",
     "decision": "Navin, 26 October 2026 (Task 046): the narration never says 'book के अनुसार', 'किताब कहती है', 'book says' or any "
                 "wording that points at the book; BIE teaches as a teacher",
     "upgraded_by": "the lesson's wording patch round: the script continues from its last answer and only the beats W-01 flags are "
                    "rewritten (bie/brain/lesson.py, reusable + script_step with start; VM job t046-v3-wording-patch)",
     "match": re.compile(r"\(W-01\)$")},
    {"rule": "S1-16", "rulebook": f"{VISION}@2026-10-21.14",
     "decision": "Navin, 27 October 2026 (Task 046 Part C addition): in an economics chapter every definition, cause-and-effect and "
                 "process item applies the concept in a real Indian situation before naming it (a place, actors, goods, numbers that "
                 "change, the mechanism step by step; economically correct, at the learner's level)",
     "upgraded_by": "the page is read again (bie/brain/understanding.py, schema bie.brain.understand-page/4); an older page of an "
                    "economics chapter is not reused",
     "match": re.compile(r"\(S1-16\)$")},
    {"rule": "S2-09", "rulebook": f"{VISION}@2026-10-21.15",
     "decision": "Navin, 29 October 2026 (verdict on Money v1): the narration's sentences are complete and natural, never a ledger's "
                 "state report ('cash ₹500 से ₹400 हुआ'); a story's numbers are said the way a teacher tells what happened",
     "upgraded_by": "the script is continued from its last answer; only the beats S2-09 flags are rewritten (bie/brain/lesson.py)",
     "match": re.compile(r"\(S2-09\)$")},
    {"rule": "W-01", "rulebook": "visual_grammar@2026-10-29.1",
     "decision": "Navin's verdict work C, 29 October 2026 (the Money lesson resume -d, v2 and v4): the narration and the screen never "
                 "say what the source lacks ('dates नहीं हैं', 'caption supplies no source'); the on-screen text is checked too",
     "upgraded_by": "the lesson's wording patch round: only the beats W-01 flags are rewritten (bie/brain/lesson.py)",
     "match": re.compile(r"\(W-01\)$")},
    {"rule": "S2-10", "rulebook": f"{VISION}@2026-10-21.16",
     "decision": "Navin's verdict work C, 29 October 2026 (the Money lesson resume -d, v10): a competitive-exam fact from outside the "
                 "book carries its dated source in the beat's `source` field",
     "upgraded_by": "the script is continued from its last answer; only the beats S2-10 flags are rewritten (bie/brain/lesson.py, "
                    "lesson-script/6)",
     "match": re.compile(r"\(S2-10\)$")},
    {"rule": "S2-08", "rulebook": f"{VISION}@2026-10-21.16",
     "decision": "Navin's verdict work C, 29 October 2026 (the Money lesson resume -d, v11 and v12): a teaching beat of the same concept "
                 "may not name the term before its example runs",
     "upgraded_by": "the script is continued from its last answer (bie/brain/lesson.py, lesson-script/6)",
     "match": re.compile(r"\(S2-08\)$")},
    {"rule": "S2-08", "rulebook": f"{VISION}@2026-10-21.14",
     "decision": "Navin, 27 October 2026 (Task 046 Part C addition): the script runs a concept's real-world example, with its "
                 "numbers, before it names the term; then the book's definition, then the real-life link",
     "upgraded_by": "the script is written again or continued from its last answer (bie/brain/lesson.py, lesson-script/5)",
     "match": re.compile(r"\(S2-08\)$")},
)


def _version(text: str, component: str = VISION) -> tuple:
    """The version tuple of one rulebook component in a full rulebook string ("content_types@…+vision-2026-10-21@…");
    a bare version ("2026-10-21.10", the sets before Task 045c) is the vision rulebook's; a missing component is ()."""
    text = text or ""
    if "@" not in text:
        return tuple(int(n) for n in re.findall(r"\d+", text)) if component == VISION else ()
    for part in text.split("+"):
        name, _, version = part.partition("@")
        if name == component:
            return tuple(int(n) for n in re.findall(r"\d+", version))
    return ()


def _changed(passed: dict, problem: str):
    """The rule change that explains ``problem`` in a set made before it, or None."""
    for change in RULE_CHANGES:
        component, _, version = change["rulebook"].partition("@")
        made = _version(passed.get("rulebook", ""), component)
        if made < _version(version) and change["match"].search(problem):
            return change
    return None


def _page_cards(record_folders) -> dict:
    """{page number: card coverage} from the process records of the runs that read the pages."""
    cards = {}
    for folder in record_folders:
        for path in sorted(Path(folder, "records").glob("understand--page-*.json")):
            record = json.loads(path.read_text(encoding="utf-8"))
            if record.get("status") == "passed" and record.get("card"):
                cards[int(record["unit"].split("-")[1])] = record["card"]["coverage"]
    return cards


def export(chapter: dict, page_blocks: dict, *, record_folders=(), lesson: dict | None = None, source: str = "",
           rulebook: str = "") -> dict:
    """The passed work of one run. ``page_blocks`` is {page number: (has image, [(block id, text), ...])}."""
    from .understanding import passed_pages

    coverage = _page_cards(record_folders)
    pages = []
    for number, value in sorted(passed_pages(chapter).items()):
        has_image, blocks = page_blocks[number]
        pages.append({"page": number, "image": bool(has_image), "blocks": [list(b) for b in blocks],
                      "coverage": coverage.get(number), "value": value})
    out = {"schema": SCHEMA, "source": source, "rulebook": rulebook,
           "course": chapter["course"], "source_sha256": chapter.get("source_sha256"), "pages": pages, "map": None, "lesson": None}
    if chapter.get("map_status") == "passed":
        out["map"] = {"items": chapter["items"], "map": chapter["map"]}
    if lesson and lesson.get("plan_status") == "passed":
        out["map"] = out["map"] or {"items": chapter["items"], "map": chapter["map"]}
        out["lesson"] = {"plan": lesson["plan"],
                         "videos": [dict(video_id=v["video_id"], title=v["title"], parts=v.get("parts") or [],
                                         beats=[{k: b[k] for k in b if k not in ("subtitle", "voice")} for b in v["beats"]])
                                    for v in lesson["videos"] if v["status"] == "passed"]}
    return out


def save(passed: dict, path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        json.dump(passed, handle, ensure_ascii=False, separators=(",", ":"))


def load(path) -> dict:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def check(passed: dict, rulebook=None) -> list:
    """Every problem today's code checks find in earlier passed work (empty: all still pass), except problems of a rule
    Navin changed after the set was made (``changed_rule_problems``)."""
    return [p for p in all_problems(passed, rulebook) if not _changed(passed, p)]


def changed_rule_problems(passed: dict, rulebook=None) -> list:
    """[(problem, rule change)] for the problems that only a later rule change finds in the set."""
    return [(p, change) for p in all_problems(passed, rulebook) for change in [_changed(passed, p)] if change]


def all_problems(passed: dict, rulebook=None) -> list:
    """Every problem today's code checks find in the set, rule changes included."""
    from . import rulebook as rulebook_module
    from .lesson import check_plan, check_script, chapter_naksha, script_card, script_prefixes, video_budget
    from .pages import Block, Page
    from .understanding import Course, check_connect, check_page

    types = ct.load()
    problems = []
    for entry in passed["pages"]:
        blocks = tuple(Block(bid, text, (0, 0, 1, 1)) for bid, text in entry["blocks"])
        page = Page(entry["page"], blocks, b"image" if entry["image"] else None)
        card = {"coverage": entry["coverage"]} if entry.get("coverage") else None
        for p in check_page(entry["value"], page, proposals=ct.propose_blocks(blocks, types), card=card, types=types):
            problems.append(f"page {entry['page']}: {p}")
    if passed.get("map"):
        items, value = passed["map"]["items"], passed["map"]["map"]
        for p in check_connect(value, items) + engines.map_checks(value, items)[0]:
            problems.append(f"map: {p}")
    if passed.get("lesson"):
        rulebook = rulebook or rulebook_module.load()
        course = Course(**passed["course"])
        chapter = {"course": passed["course"], "items": passed["map"]["items"], "map": passed["map"]["map"],
                   "source_sha256": passed.get("source_sha256")}
        plan = passed["lesson"]["plan"]
        for p in check_plan(plan, chapter):
            problems.append(f"plan: {p}")
        naksha = chapter_naksha(chapter)
        prefix = script_prefixes(course, rulebook)[0]
        videos = {v["video_id"]: v for v in plan["videos"]}
        for video in passed["lesson"]["videos"]:
            card = script_card(course, chapter, naksha, plan, videos[video["video_id"]], rulebook=rulebook, prefix=prefix)
            value = {"notes": None, "title": video["title"], "parts": video["parts"], "beats": video["beats"]}
            budget = video_budget(chapter, plan["videos"], videos[video["video_id"]])
            for p in check_script(value, chapter, videos[video["video_id"]], course.language, card, budget):
                problems.append(f"script {video['video_id']}: {p}")
    return problems
