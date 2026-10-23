"""Passed outputs stay passed: today's code checks re-run on everything that passed in earlier live runs.

Navin's standing rule "seekh → code" (CLAUDE.md, 23 October 2026) lets Claude turn reviewer findings that repeated
into new code checks without asking, on one condition: a new check must not fail any output that passed before.
This module keeps that promise checkable. ``export`` turns a run's passed work into a compact set (``bie.brain.
passed-outputs/1``): every passed page's items with the page's native text blocks and the card's coverage, the
chapter map when it passed, the lesson plan and every passed script. ``check`` runs today's code checks (the same
functions the section runner uses) on such a set and returns every problem; an empty list means every earlier
passed output still passes. The sets live in ``tests/fixtures/passed_outputs/`` and a test runs them all.

These sets are BIE's own outputs kept for regression; they are not accepted examples (that needs Navin's verdict).
"""
from __future__ import annotations

import gzip
import json
from pathlib import Path

from . import content_types as ct
from . import engines

SCHEMA = "bie.brain.passed-outputs/1"


def _page_cards(record_folders) -> dict:
    """{page number: card coverage} from the process records of the runs that read the pages."""
    cards = {}
    for folder in record_folders:
        for path in sorted(Path(folder, "records").glob("understand--page-*.json")):
            record = json.loads(path.read_text(encoding="utf-8"))
            if record.get("status") == "passed" and record.get("card"):
                cards[int(record["unit"].split("-")[1])] = record["card"]["coverage"]
    return cards


def export(chapter: dict, page_blocks: dict, *, record_folders=(), lesson: dict | None = None, source: str = "") -> dict:
    """The passed work of one run. ``page_blocks`` is {page number: (has image, [(block id, text), ...])}."""
    from .understanding import passed_pages

    coverage = _page_cards(record_folders)
    pages = []
    for number, value in sorted(passed_pages(chapter).items()):
        has_image, blocks = page_blocks[number]
        pages.append({"page": number, "image": bool(has_image), "blocks": [list(b) for b in blocks],
                      "coverage": coverage.get(number), "value": value})
    out = {"schema": SCHEMA, "source": source, "course": chapter["course"], "source_sha256": chapter.get("source_sha256"),
           "pages": pages, "map": None, "lesson": None}
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
    """Every problem today's code checks find in earlier passed work (empty: all still pass)."""
    from . import rulebook as rulebook_module
    from .lesson import check_plan, check_script, chapter_naksha, script_card, script_prefixes
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
            for p in check_script(value, chapter, videos[video["video_id"]], course.language, card):
                problems.append(f"script {video['video_id']}: {p}")
    return problems
