"""The notes-page slot (Phase 1, part B4; agreement of 3 November 2026, deliverable table: one question per page,
answered by a picture, a flow, a comparison or a table, built from the same saanche as the video).

A page (``bie.notes-page/1``) is what BIE's AI writes per chapter question. ``problems()`` names everything wrong
exactly; a ``picture`` page's drawing is a one-scene show-spec (``still_spec()``) that the showing engine renders —
the same saanche, people and texts as the video, so the notes look like the lesson. ``deck_of()`` turns pages into
the existing notes deck (``bie/brain/notes_render.py``, phone first, print view is the PDF): no parallel renderer.
"""
from __future__ import annotations

from bie.brain import saanche
from bie.brain.notes import ASKS

KINDS = ("picture", "flow", "compare", "table")
STAGE_W, STAGE_H = 1920, 1080
FLOOR_PX = 36


def _rows(page, key):
    return page.get(key) or []


def problems(page: dict) -> list:
    """Why this page cannot be made, each problem naming the field exactly (never a crash, whatever the shape)."""
    if not isinstance(page, dict):
        return [f"a notes page must be a JSON object, not {type(page).__name__}"]
    out = []
    pid = page.get("page_id") or "?"
    if str(page.get("schema", "")) != "bie.notes-page/1":
        out.append(f"page {pid}: schema must be bie.notes-page/1")
    for key in ("page_id", "question", "essence", "answer"):
        if not page.get(key):
            out.append(f"page {pid}: '{key}' is needed")
    if page.get("ask") not in ASKS:
        out.append(f"page {pid}: no ask '{page.get('ask')}' (asks: {', '.join(ASKS)})")
    if not _rows(page, "item_ids"):
        out.append(f"page {pid}: 'item_ids' is needed (the book items this page answers from)")
    visual = page.get("visual") or {}
    if not isinstance(visual, dict):
        out.append(f"page {pid}: 'visual' must be a JSON object, not {type(visual).__name__}")
        return out
    kind = visual.get("kind")
    if kind not in KINDS:
        out.append(f"page {pid}: no visual kind '{kind}' (kinds: {', '.join(KINDS)})")
        return out
    if kind == "picture":
        els = visual.get("els") or []
        if not isinstance(els, list):
            out.append(f"page {pid}: 'els' must be a list of JSON objects, not {type(els).__name__}")
            return out
        if not els:
            out.append(f"page {pid}: a picture needs 'els' (the plan language's things and texts)")
        for i, el in enumerate(els):
            where = f"page {pid} picture el {i + 1}"
            if not isinstance(el, dict):
                out.append(f"{where}: an el must be a JSON object, not {type(el).__name__}")
                continue
            if el.get("draw") and not str(el["draw"]).startswith("__"):
                for p in saanche.problems(el["draw"], el.get("p") or {}):
                    out.append(f"{where}: {p}")
            elif el.get("text") is not None:
                if float(el.get("size", 46)) < FLOOR_PX:
                    out.append(f"{where}: text '{el['text']}' is under the {FLOOR_PX}px floor (CV-17)")
            elif not (el.get("asset") or el.get("group") or str(el.get("draw", "")).startswith("__") or el.get("kind")):
                out.append(f"{where}: not a thing (draw/asset/group/mini) and not a text")
            if el.get("draw") or el.get("asset") or el.get("group") or el.get("text") is not None:
                x, y = el.get("x"), el.get("y")
                if not (isinstance(x, (int, float)) and isinstance(y, (int, float))):
                    out.append(f"{where}: x and y on the {STAGE_W}x{STAGE_H} stage are needed")
                elif not (0 <= x <= STAGE_W and 0 <= y <= STAGE_H):
                    out.append(f"{where}: ({x}, {y}) is off the {STAGE_W}x{STAGE_H} stage")
    elif kind == "flow":
        steps = visual.get("steps") or []
        if not isinstance(steps, list) or any(not isinstance(s, dict) for s in steps):
            out.append(f"page {pid}: 'steps' must be a list of JSON objects")
            return out
        if len(steps) < 2:
            out.append(f"page {pid}: a flow needs at least 2 steps")
        for s in steps:
            if not s.get("label"):
                out.append(f"page {pid}: a flow step without a label")
    elif kind == "compare":
        columns, rows = visual.get("columns") or [], visual.get("rows") or []
        if not isinstance(columns, list) or not isinstance(rows, list) or any(not isinstance(r, dict) for r in rows):
            out.append(f"page {pid}: 'columns' must be a list of strings and 'rows' a list of JSON objects")
            return out
        if len(columns) < 2:
            out.append(f"page {pid}: a comparison needs at least 2 columns")
        if not rows:
            out.append(f"page {pid}: a comparison needs rows")
        for r in rows:
            if len(r.get("cells") or []) != len(columns):
                out.append(f"page {pid}: row '{r.get('label')}' has {len(r.get('cells') or [])} cells for "
                           f"{len(columns)} columns")
    else:
        rows = visual.get("rows") or []
        if not isinstance(rows, list) or any(not isinstance(r, dict) for r in rows):
            out.append(f"page {pid}: 'rows' must be a list of JSON objects")
            return out
        if not rows:
            out.append(f"page {pid}: a table needs rows")
        for r in rows:
            if not r.get("label"):
                out.append(f"page {pid}: a table row without a label")
    return out


def still_spec(page: dict, *, width: int = 1280, height: int = 720, assets: dict | None = None) -> dict:
    """A picture page's drawing as a one-scene show-spec: the showing engine renders the page's picture."""
    visual = page.get("visual") or {}
    els = []
    for el in visual.get("els") or []:
        el = dict(el)
        # a still is the finished picture: everything is already there (a word does not pop in, an arrow is drawn,
        # a mark is ticked) - the engine animates from t0, so t0 lies well before the frame (Sloman ch2 notes: words
        # and arrows were invisible at frame 0)
        el["t0"] = min(float(el.get("t0") or 0.0), 0.0) - 5.0
        el.setdefault("t1", None)
        el["enter"] = "none"
        if el.get("text") is None and "keys" not in el and not el.get("kind"):
            el["keys"] = []
        if el.get("text") is None and not el.get("kind") and "s" not in el:
            el["s"] = 1
        if el.get("text") is None and not el.get("kind") and "z" not in el:
            el["z"] = 20
        if el.get("text") is not None:
            el.setdefault("z", 40)
        els.append(el)
    spec = {"schema": "bie.show-spec/1", "fps": 30, "width": width, "height": height, "duration": 1.0,
            "subs": [], "assets": assets or {},
            "scenes": [{"id": page.get("page_id", "page"), "t0": 0.0, "t1": 1.0,
                        "bg": visual.get("bg", "paper"), "cam": [], "els": els}]}
    from bie.brain import formats
    formats.check("show_spec", spec, where=f"notes page {page.get('page_id')}")
    return spec


def slide_of(page: dict, image_src: str | None = None) -> dict:
    """One slide of the existing notes deck from a page; a picture page points at its rendered still."""
    visual = page.get("visual") or {}
    kind = visual.get("kind")
    if kind == "picture":
        v = {"type": "image", "src": image_src or "", "alt": page.get("question", ""),
             "caption": visual.get("caption", ""), "title": visual.get("title", "")}
    elif kind == "flow":
        v = {"type": "flow", "title": visual.get("title", ""),
             "steps": [{"label": s.get("label", ""), "detail": s.get("detail", "")} for s in visual.get("steps") or []]}
    elif kind == "compare":
        v = {"type": "difference_table", "title": visual.get("title", ""), "columns": list(visual.get("columns") or []),
             "rows": [{"label": r.get("label", ""), "cells": list(r.get("cells") or [])} for r in visual.get("rows") or []]}
    else:
        v = {"type": "labelled_list", "title": visual.get("title", ""),
             "nodes": [{"id": r.get("label", ""), "label": r.get("label", ""), "parent_id": "",
                        "detail": " · ".join(str(c) for c in (r.get("cells") or []) if c) or r.get("detail", "")}
                       for r in visual.get("rows") or []]}
    return {"slide_id": page["page_id"], "ask": page.get("ask", "what"), "question": page.get("question", ""),
            "essence": page.get("essence", ""), "answer": page.get("answer", ""),
            "deep_dive": page.get("deep_dive", ""), "visual": v,
            "source_item_ids": list(page.get("item_ids") or []), "basis": page.get("basis", "book"),
            "not_in_book": page.get("not_in_book", ""), "pyq_item_ids": list(page.get("pyq_item_ids") or [])}


def deck_of(pages: list, *, course: dict, chapter_name: str, items: dict | None = None,
            images: dict | None = None, rulebook_version: str = "") -> dict:
    """The pages as the existing notes deck's input (``render_notes_html`` plays it; print view is the PDF)."""
    bad = [p for page in pages for p in problems(page)]
    if bad:
        raise ValueError("pages not makeable:\n- " + "\n- ".join(bad))
    images = images or {}
    slides = [slide_of(page, images.get(page["page_id"])) for page in pages]
    return {"course": course, "rulebook_version": rulebook_version,
            "concepts": [{"name": chapter_name, "slides": slides}], "items": items or {}}
