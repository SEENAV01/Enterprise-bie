"""Phase 1, part C (second slice): BIE's AI writes the notes pages and the game levels in the new slots.

Two writer steps per chapter, both judged by the slot validators of parts B3 and B4 (every problem named exactly,
the maker patches): ``run_notes_pages`` writes ``bie.notes-page/1`` pages (one question per page; picture pages
draw with the showing engine's saanche) and the phone deck; ``run_game_levels`` writes ``bie.game-level/1`` levels
(the five mechanics; a video's story becomes a level) and the playable phone game. Extends the notes and game
sections of Sections 6 and 7 — the designs stay theirs; these write the new page and level formats.
"""
from __future__ import annotations

import json
from pathlib import Path

from .common import S, arr, fmt, obj
from .runner import NOTES_SCHEMA, Step
from .understanding import Course
from bie.brain import formats, game_levels, notes_pages
from bie.brain.game_runtime import render_game_html
from bie.brain.notes_render import render_notes_html

PAGES_SCHEMA = obj({"notes": NOTES_SCHEMA, "pages": arr({"type": "object"})})
PAGES_PATCH = obj({"notes": NOTES_SCHEMA, "replace_pages": arr({"type": "object"}), "remove_page_ids": arr(S)})
LEVELS_SCHEMA = obj({"notes": NOTES_SCHEMA, "levels": arr({"type": "object"})})
LEVELS_PATCH = obj({"notes": NOTES_SCHEMA, "replace_levels": arr({"type": "object"}), "remove_level_ids": arr(S)})

PAGES_ROLE = """You are BIE's notes-page writer for a {subject} chapter for {learners}. One question per page, the way Navin
designed revision: question, essence (one line), answer (short), deep_dive (optional), and ONE visual that answers it —
"picture" (the showing engine draws it: els = saanche/mini-people/texts on the 1920x1080 stage, texts >= 36px; the same
drawings as the lesson video), "flow" (steps), "compare" (columns + rows) or "table" (rows). Schema bie.notes-page/1.
Every page names the item_ids it answers from; every teachable concept of the chapter gets at least one page; nothing
invented beyond the items given. Saanche you may draw: {saanche}.
{rules}"""

LEVELS_ROLE = """You are BIE's game-level writer for a {subject} chapter for {learners}: padhai hi game - the student acts and
the process happens. Schema bie.game-level/1, mechanics: run_process (steps in order), place_right (things to places),
build_timeline (order of events, decoys break it), find_partner (match who fits whom), cause_effect (chain), act_as (the
student is a character or institution - role, situation, 2-4 choices each with correct true/false and feedback; a wrong
choice says what breaks and why) and predict (the student sets a number first - slider: label, unit, min, max, step, answer,
tolerance, predict_prompt, reveal_label; feedback_close, feedback_far). A drag level (the first five): instruction in simple
Hinglish, 2-7 pieces (labels <= 44 characters, a phone screen), every right move says what happens, every wrong move and
decoy says what breaks and why. Every level: win line and the item_ids it makes the student play. Use at least two
different mechanics across the levels; build levels from the chapter's own stories and processes, nothing invented.
A drag level may happen in a world (the same places the videos use): world = {{"kind": ..., "signs": "a;b;c", ...}} with
the world saancha's parameters, and in place_right / find_partner each place may sit on a spot of it ("spot": "counter2"
or a sign's words) - e.g. drop each customer's need on the right counter of the bank hall. Worlds and spots: {worlds}.
{rules}"""


def _items_payload(chapter: dict) -> list:
    return [{"item_id": iid, "content": item.get("content", "")[:300], "kind": item.get("kind", ""),
             "content_type": item.get("content_type", "")}
            for iid, item in (chapter.get("items") or {}).items() if item.get("teachable")]


def _concepts_payload(chapter: dict) -> list:
    return [{"concept_id": c["concept_id"], "name": c["name"], "item_ids": c["item_ids"]}
            for c in (chapter.get("map") or {}).get("concepts") or []]


def check_pages(value: dict, chapter: dict) -> list:
    problems = []
    pages = value.get("pages") or []
    known = {iid for iid, item in (chapter.get("items") or {}).items()}
    seen = set()
    for page in pages:
        if not isinstance(page, dict):
            problems.append(f"every page must be a JSON object, not {type(page).__name__}")
            continue
        problems += [p for p in formats.problems("notes_page", page)]
        problems += notes_pages.problems(page)
        pid = page.get("page_id")
        if pid in seen:
            problems.append(f"two pages named '{pid}'")
        seen.add(pid)
        for iid in page.get("item_ids") or []:
            if iid not in known:
                problems.append(f"page {pid}: item '{iid}' is not in the chapter")
    covered = {iid for page in pages if isinstance(page, dict) for iid in page.get("item_ids") or []}
    for c in _concepts_payload(chapter):
        if not any(iid in covered for iid in c["item_ids"]):
            problems.append(f"concept '{c['name']}' ({c['concept_id']}) has no page")
    if not pages:
        problems.append("no pages")
    return sorted(set(problems))[:40]


def check_levels(value: dict, chapter: dict) -> list:
    problems = []
    levels = value.get("levels") or []
    known = set((chapter.get("items") or {}))
    seen = set()
    for level in levels:
        if not isinstance(level, dict):
            problems.append(f"every level must be a JSON object, not {type(level).__name__}")
            continue
        problems += [p for p in formats.problems("game_level", level)]
        problems += game_levels.problems(level)
        lid = level.get("level_id")
        if lid in seen:
            problems.append(f"two levels named '{lid}'")
        seen.add(lid)
        for iid in level.get("item_ids") or []:
            if iid not in known:
                problems.append(f"level {lid}: item '{iid}' is not in the chapter")
    if len(levels) < 2:
        problems.append("at least 2 levels are needed")
    elif len({l.get("mechanic") for l in levels if isinstance(l, dict)}) < 2:
        problems.append("use at least two different mechanics across the levels")
    return sorted(set(problems))[:40]


def _patch(key_replace, key_remove, id_key):
    def apply(previous: dict, patch: dict) -> dict:
        rows = {r.get(id_key): r for r in previous.get("pages" if id_key == "page_id" else "levels") or []}
        for r in patch.get(key_replace) or []:
            rows[r.get(id_key)] = r
        for rid in patch.get(key_remove) or []:
            rows.pop(rid, None)
        out = dict(previous)
        out["pages" if id_key == "page_id" else "levels"] = list(rows.values())
        return out
    return apply


def page_shape_text() -> str:
    """The exact page shape in the prompt, built from the real constants so it can never drift: the first live
    notespages run lost its whole first round to fields the role never named (every page missing ask and
    visual.kind)."""
    from bie.brain.notes import ASKS
    return ("A page's exact shape (bie.notes-page/1), every required key present:\n"
            + json.dumps(formats.NOTES_PAGE, ensure_ascii=False)
            + f"\nask is one of: {', '.join(ASKS)}."
            + "\nvisual by kind: picture needs els (each el a JSON object on the 1920x1080 stage); flow needs steps"
              " (each a JSON object with label); compare needs columns (strings) and rows (each a JSON object with"
              " label and cells, one cell per column); table needs rows (each a JSON object with label)."
            + "\nquestion, essence, answer and deep_dive are plain strings, never objects or lists.")


def pages_step(course: Course, chapter: dict, *, rulebook, max_rounds: int = 4, start: dict | None = None) -> Step:
    from bie.brain import saanche
    system = fmt(PAGES_ROLE, course, saanche=", ".join(saanche.names()), rules=rulebook.instructions("notes"))
    user = (f"Chapter: {(chapter.get('map') or {}).get('chapter_title', course.title)}.\n"
            f"Concepts: {json.dumps(_concepts_payload(chapter), ensure_ascii=False)}\n"
            f"Teachable items: {json.dumps(_items_payload(chapter), ensure_ascii=False)}\n\n"
            f"{page_shape_text()}\n\n"
            "Reply with {\"notes\": ..., \"pages\": [bie.notes-page/1 ...]}.")
    return Step(section="notespages", unit="pages", instructions_version="notes-pages/1", system=system, user=user,
                schema=PAGES_SCHEMA, check=lambda value: check_pages(value, chapter),
                patch_schema=PAGES_PATCH, apply_patch=_patch("replace_pages", "remove_page_ids", "page_id"),
                patch_hint="Reply with a patch: replace_pages (same page_id replaces), remove_page_ids.",
                max_rounds=max_rounds, start=start)


def levels_step(course: Course, chapter: dict, *, rulebook, max_rounds: int = 4, start: dict | None = None) -> Step:
    system = fmt(LEVELS_ROLE, course, rules=rulebook.instructions("game"), worlds=game_levels.world_spots_text())
    user = (f"Chapter: {(chapter.get('map') or {}).get('chapter_title', course.title)}.\n"
            f"Teachable items: {json.dumps(_items_payload(chapter), ensure_ascii=False)}\n\n"
            "Reply with {\"notes\": ..., \"levels\": [bie.game-level/1 ...]}.")
    return Step(section="gamelevels", unit="levels", instructions_version="game-levels/1", system=system, user=user,
                schema=LEVELS_SCHEMA, check=lambda value: check_levels(value, chapter),
                patch_schema=LEVELS_PATCH, apply_patch=_patch("replace_levels", "remove_level_ids", "level_id"),
                patch_hint="Reply with a patch: replace_levels (same level_id replaces), remove_level_ids.",
                max_rounds=max_rounds, start=start)


def run_notes_pages(chapter: dict, course: Course, runner, out_dir, *, max_rounds: int = 4) -> dict:
    out = Path(out_dir)
    (out / "notes" / "pages").mkdir(parents=True, exist_ok=True)
    result = runner.run(pages_step(course, chapter, rulebook=runner.rulebook, max_rounds=max_rounds))
    summary = {"status": result.status, "rounds": len(result.rounds), "pages": 0, "pictures": 0}
    if result.status == "passed" and result.output:
        pages = result.output["pages"]
        for page in pages:
            (out / "notes" / "pages" / f"{page['page_id']}.json").write_text(
                json.dumps(page, ensure_ascii=False, indent=1), encoding="utf-8")
        images = {p["page_id"]: f"pages/{p['page_id']}.png" for p in pages
                  if (p.get("visual") or {}).get("kind") == "picture"}
        deck = notes_pages.deck_of(pages, course=dict(title=course.title, subject=course.subject,
                                                      learners=course.learners, language=course.language),
                                   chapter_name=(chapter.get("map") or {}).get("chapter_title", course.title),
                                   items={iid: {"page": item.get("page") or 0}
                                          for iid, item in (chapter.get("items") or {}).items()},
                                   images=images, rulebook_version=runner.rulebook.version)
        (out / "notes" / "NOTES_PAGES.html").write_text(render_notes_html(deck), encoding="utf-8")
        summary.update(pages=len(pages), pictures=len(images))
    (out / "notes" / "pages_summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    return summary


def run_game_levels(chapter: dict, course: Course, runner, out_dir, *, max_rounds: int = 4) -> dict:
    out = Path(out_dir)
    (out / "game" / "levels").mkdir(parents=True, exist_ok=True)
    result = runner.run(levels_step(course, chapter, rulebook=runner.rulebook, max_rounds=max_rounds))
    summary = {"status": result.status, "rounds": len(result.rounds), "levels": 0, "mechanics": []}
    if result.status == "passed" and result.output:
        levels = result.output["levels"]
        for level in levels:
            (out / "game" / "levels" / f"{level['level_id']}.json").write_text(
                json.dumps(level, ensure_ascii=False, indent=1), encoding="utf-8")
        title = (chapter.get("map") or {}).get("chapter_title", course.title)
        mission = game_levels.mission_of(levels, title=f"{title}: khel kar seekho")
        html = render_game_html({"id": f"game-{title[:20]}", "title": title, "world": "",
                                 "missions": [mission], "credits": []})
        (out / "game" / "GAME.html").write_text(html, encoding="utf-8")
        summary.update(levels=len(levels), mechanics=sorted({l["mechanic"] for l in levels}))
    (out / "game" / "levels_summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    return summary
