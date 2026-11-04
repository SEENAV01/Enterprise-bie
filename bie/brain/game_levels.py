"""The game-level slot (Phase 1, part B3; agreement of 3 November 2026, decision 6: a video's story becomes a game
level — "padhai hi game").

A level (``bie.game-level/1``) is what BIE's AI writes from a chapter's story: one of five mechanics with the
mechanic's own natural fields. ``problems()`` names everything wrong exactly (the writer fixes its level without
guessing), and ``stage_of()`` lowers a level to one stage of the existing phone runtime
(``bie/brain/game_runtime.py``: the drag engine plays all five — ordered for processes, timelines and chains,
unordered for placing and partner-finding), so one runtime plays every level ("reuse, do not duplicate").

The five mechanics (from the agreement's list):
- ``run_process``: do the steps in the order the process really runs; out of order breaks it.
- ``place_right``: put every thing where it belongs; a wrong place shows what breaks and why.
- ``build_timeline``: build the order of events; a wrong pick breaks the timeline (decoys allowed).
- ``find_partner``: match each seeker with the partner that fits (barter's double coincidence); a wrong match
  names what is missing.
- ``cause_effect``: build the chain from cause to effect; a wrong link shows why the chain breaks.
"""
from __future__ import annotations

MECHANICS = ("run_process", "place_right", "build_timeline", "find_partner", "cause_effect")
MAX_PIECES = 7          # a phone screen holds this many tokens or places comfortably
MAX_LABEL = 44

ORDERED = {"run_process": True, "place_right": False, "build_timeline": True, "find_partner": False, "cause_effect": True}
SLOT_WORD = {"run_process": "कदम", "build_timeline": "पहले → बाद", "cause_effect": "कारण → असर"}


def _rows(level, key):
    return level.get(key) or []


def problems(level: dict) -> list:
    """Why this level cannot be played, each problem naming the field exactly (never a crash, whatever the shape)."""
    if not isinstance(level, dict):
        return [f"a game level must be a JSON object, not {type(level).__name__}"]
    out = []
    lid = level.get("level_id") or "?"

    def need(key, kind=str):
        v = level.get(key)
        if not v or not isinstance(v, kind):
            out.append(f"level {lid}: '{key}' is needed")
        return v

    if str(level.get("schema", "")) != "bie.game-level/1":
        out.append(f"level {lid}: schema must be bie.game-level/1")
    need("level_id")
    need("title")
    need("instruction")
    mech = level.get("mechanic")
    if mech not in MECHANICS:
        out.append(f"level {lid}: no mechanic '{mech}' (mechanics: {', '.join(MECHANICS)})")
        return out
    pieces = _rows(level, "pieces")
    places = _rows(level, "places") if mech in ("place_right", "find_partner") else []
    for kind, rows in (("pieces", pieces), ("places", places)):
        if not isinstance(rows, list):
            out.append(f"level {lid}: '{kind}' must be a list of JSON objects, not {type(rows).__name__}")
        else:
            out += [f"level {lid}: every one of '{kind}' must be a JSON object, not {type(row).__name__}"
                    for row in rows if not isinstance(row, dict)]
    pieces = [p for p in pieces if isinstance(p, dict)] if isinstance(pieces, list) else []
    places = [p for p in places if isinstance(p, dict)] if isinstance(places, list) else []
    if not 2 <= len(pieces) <= MAX_PIECES:
        out.append(f"level {lid}: 2..{MAX_PIECES} pieces are needed, not {len(pieces)} (a phone screen)")
    if mech in ("place_right", "find_partner") and not 2 <= len(places) <= MAX_PIECES:
        out.append(f"level {lid}: 2..{MAX_PIECES} places are needed, not {len(places)}")
    seen = set()
    for row, kind in [(p, "piece") for p in pieces] + [(p, "place") for p in places]:
        rid = row.get("id")
        if not rid:
            out.append(f"level {lid}: a {kind} without an id")
            continue
        if rid in seen:
            out.append(f"level {lid}: two pieces or places named '{rid}'")
        seen.add(rid)
        if not row.get("label"):
            out.append(f"level {lid}: {kind} '{rid}' has no label")
        elif len(str(row["label"])) > MAX_LABEL:
            out.append(f"level {lid}: {kind} '{rid}' label is over {MAX_LABEL} characters (a phone token)")
    ordered_pieces = [p for p in pieces if not p.get("decoy")]
    if mech in ("run_process", "build_timeline", "cause_effect"):
        if len(ordered_pieces) < 2:
            out.append(f"level {lid}: at least 2 non-decoy pieces in order are needed")
        for p in ordered_pieces:
            if not p.get("right"):
                out.append(f"level {lid}: piece '{p.get('id')}' needs 'right' (what happens when it lands right)")
        for p in pieces:
            if p.get("decoy") and not p.get("wrong"):
                out.append(f"level {lid}: decoy '{p.get('id')}' needs 'wrong' (why it breaks the {mech})")
    else:
        fits = {p.get("fits") for p in pieces if not p.get("decoy")}
        place_ids = {p.get("id") for p in places}
        for p in pieces:
            if p.get("decoy"):
                if not p.get("wrong"):
                    out.append(f"level {lid}: decoy '{p.get('id')}' needs 'wrong'")
                continue
            if p.get("fits") not in place_ids:
                out.append(f"level {lid}: piece '{p.get('id')}' fits '{p.get('fits')}', which is no place")
            if not p.get("right"):
                out.append(f"level {lid}: piece '{p.get('id')}' needs 'right'")
            if not p.get("wrong"):
                out.append(f"level {lid}: piece '{p.get('id')}' needs 'wrong' (what breaks on a wrong {('match' if mech == 'find_partner' else 'place')})")
        if fits and len(fits) < len([p for p in pieces if not p.get("decoy")]):
            pass  # two pieces may share a place (a heap takes many things)
    if not level.get("win"):
        out.append(f"level {lid}: 'win' is needed (what the student made work)")
    if not _rows(level, "item_ids"):
        out.append(f"level {lid}: 'item_ids' is needed (the book items this level makes the student play)")
    return out


def stage_of(level: dict) -> dict:
    """One runtime stage (the drag engine) from a valid level; ``problems()`` must be empty first."""
    mech = level["mechanic"]
    pieces = _rows(level, "pieces")
    real = [p for p in pieces if not p.get("decoy")]
    tokens = [{"id": p["id"], "label": str(p["label"])} for p in pieces]
    rules = []
    if mech in ("run_process", "build_timeline", "cause_effect"):
        word = SLOT_WORD[mech]
        targets = [{"id": f"slot{i + 1}", "label": f"{i + 1}. {word}", "box": {"x": 0, "y": 0, "w": 0, "h": 0}}
                   for i in range(len(real))]
        for i, p in enumerate(real):
            rules.append({"token": p["id"], "target": f"slot{i + 1}", "correct": True,
                          "feedback": str(p["right"]), "effect": "flow"})
            for j in range(len(real)):
                if j != i:
                    rules.append({"token": p["id"], "target": f"slot{j + 1}", "correct": False,
                                  "feedback": str(p.get("wrong") or f"'{p['label']}' yahan nahi aata: {level.get('order_why', 'kram wahi chalta hai jaise asli mein hota hai.')}"),
                                  "effect": "break"})
        for p in pieces:
            if p.get("decoy"):
                for j in range(len(real)):
                    rules.append({"token": p["id"], "target": f"slot{j + 1}", "correct": False,
                                  "feedback": str(p["wrong"]), "effect": "shake"})
    else:
        places = _rows(level, "places")
        targets = [{"id": p["id"], "label": str(p["label"]), "box": {"x": 0, "y": 0, "w": 0, "h": 0}} for p in places]
        for p in real:
            for place in places:
                if place["id"] == p["fits"]:
                    rules.append({"token": p["id"], "target": place["id"], "correct": True,
                                  "feedback": str(p["right"]), "effect": "glow"})
                else:
                    rules.append({"token": p["id"], "target": place["id"], "correct": False,
                                  "feedback": str(p["wrong"]), "effect": "break"})
        for p in pieces:
            if p.get("decoy"):
                for place in places:
                    rules.append({"token": p["id"], "target": place["id"], "correct": False,
                                  "feedback": str(p["wrong"]), "effect": "shake"})
    return {"stage_id": level["level_id"], "kind": "drag", "instruction": str(level["instruction"]),
            "tokens": tokens, "targets": targets, "rules": rules, "ordered": bool(ORDERED[mech]),
            "situation": "", "choices": [],
            "slider": {"label": "", "unit": "", "min": 0, "max": 0, "step": 0, "answer": 0, "tolerance": 0,
                       "predict_prompt": "", "reveal_label": "", "data": []},
            "feedback_close": "", "feedback_far": "", "item_ids": list(level.get("item_ids") or [])}


def mission_of(levels: list, *, title: str, intro: str = "", win_text: str = "") -> dict:
    """One playable mission from levels (each level one stage), for the existing runtime and bot."""
    bad = [p for level in levels for p in problems(level)]
    if bad:
        raise ValueError("levels not playable:\n- " + "\n- ".join(bad))
    return {"mission_id": "-".join(l["level_id"] for l in levels)[:60] or "level", "title": title, "intro": intro,
            "stages": [stage_of(l) for l in levels], "win_text": win_text or levels[-1].get("win", ""),
            "replay_twist": "shuffle_tokens",
            "item_ids": sorted({i for l in levels for i in l.get("item_ids") or []})}
