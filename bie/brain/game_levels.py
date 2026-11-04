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

Two more, learned from 54 economy reference videos (4 Nov 2026; their game ideas were mostly "be the actor and
decide" and "set the number and see what happens"), played by the runtime's existing branch and slider stages:
- ``act_as``: the student is a character or an institution (RBI, a founder, a bank officer, the GDP counter) in a
  situation and chooses; every wrong choice says what breaks and why.
- ``predict``: the student sets a number first (how much goes into the CRR vault, the yield at a price, the
  per-person income), then sees the real value and the relationship; close and far guesses get their own feedback.

A level can happen in a world (4 Nov 2026): ``world`` names one of the economy worlds of the showing engine (a bank
hall, a market, a port, ...) with its parameters (the saancha manifest is the law), and each place of
``place_right`` / ``find_partner`` can sit on a ``spot`` of that world (counter2, the vault, a stall's sign words), so
the student drops the customer's need on the right counter of a real-looking bank hall. The runtime draws the world
with the same code as the videos (``worlds.mjs``) and puts the drop zones on the spots.
"""
from __future__ import annotations

MECHANICS = ("run_process", "place_right", "build_timeline", "find_partner", "cause_effect", "act_as", "predict")
DRAG = ("run_process", "place_right", "build_timeline", "find_partner", "cause_effect")
MAX_CHOICES = 4
MAX_PIECES = 7          # a phone screen holds this many tokens or places comfortably
MAX_LABEL = 44

ORDERED = {"run_process": True, "place_right": False, "build_timeline": True, "find_partner": False, "cause_effect": True}
SLOT_WORD = {"run_process": "कदम", "build_timeline": "पहले → बाद", "cause_effect": "कारण → असर"}


def _rows(level, key):
    return level.get(key) or []


# The spots of every world, by name (the same names worlds.mjs worldSpots gives; tests/test_p1_game_levels.py keeps
# them equal). Numbered spots take their count from the world's parameters exactly as the drawing does.
_FIXED_SPOTS = {"market": ("floor",), "bankHall": ("vault", "queue", "floor"), "centralBank": ("vault", "floor"),
                "exchangeFloor": ("board", "desks", "floor"), "port": ("ship", "crane", "dock"), "factory": ("belt", "chimney"),
                "village": ("field", "hut", "well", "tree"), "office": ("floor",), "court": ("bench", "left", "right", "floor"),
                "city": ("road",), "assembly": ("podium", "seats", "floor"), "twoCountries": ("left", "right", "border", "road"),
                "forexCounter": ("counter", "board", "queue", "floor")}
_NUMBERED = {"market": ("stall", 4, 2, 6), "bankHall": ("counter", 3, 1, 5), "office": ("desk", 5, 1, 6),
             "factory": ("shed", 3, 3, 3), "city": ("shop", 3, 3, 3)}
_NAMED = {"twoCountries": ("left", "right")}             # the first signs name these fixed spots (the two countries)


def world_spot_names(world: dict) -> list:
    """The spot names of a world (fixed spots, numbered spots, then the words of the signs on numbered spots)."""
    kind = world.get("kind") if world.get("kind") in _FIXED_SPOTS else "market"
    signs = [t.strip() for t in str(world.get("signs") or "").split(";") if t.strip()]
    names = list(_FIXED_SPOTS[kind])
    if kind in _NUMBERED:
        pre, d, lo, hi = _NUMBERED[kind]
        c = world.get("count")
        n = c if isinstance(c, (int, float)) and not isinstance(c, bool) and c > 0 else (len(signs) or d)
        n = max(lo, min(hi, int(round(n))))
        names += [f"{pre}{i + 1}" for i in range(n)]
        for sg in signs[:n]:
            if sg not in names:
                names.append(sg)
    for sg in signs[:len(_NAMED.get(kind, ()))]:
        if sg not in names:
            names.append(sg)
    return names


def world_spots_text() -> str:
    """One line per world for the level writer: its spots (numbered ones count by the world's signs or count)."""
    rows = []
    for kind, fixed in _FIXED_SPOTS.items():
        num = _NUMBERED.get(kind)
        spots = ([f"{num[0]}1..{num[0]}{num[3]} (one per sign; a sign's words work too)"] if num and num[3] > num[2]
                 else [f"{num[0]}1..{num[0]}{num[3]} (a sign's words work too)"] if num else []) + list(fixed)
        if kind in _NAMED:
            spots.append(f"(signs name {' and '.join(_NAMED[kind])})")
        rows.append(f"{kind}: {', '.join(spots)}")
    return "; ".join(rows)


def _world_problems(level: dict, lid: str) -> list:
    world = level.get("world")
    if world is None:
        return [f"level {lid}: place '{p.get('id')}' has a spot but the level has no world"
                for p in _rows(level, "places") if isinstance(p, dict) and p.get("spot")]
    if not isinstance(world, dict):
        return [f"level {lid}: 'world' must be a JSON object (kind, signs, ...), not {type(world).__name__}"]
    from bie.brain import saanche
    out = [f"level {lid}: world: {p}" for p in saanche.problems("world", world)]
    names = world_spot_names(world)
    for p in _rows(level, "places"):
        if isinstance(p, dict) and p.get("spot") and p["spot"] not in names:
            out.append(f"level {lid}: place '{p.get('id')}' spot '{p['spot']}' is not in the {world.get('kind', 'market')} "
                       f"world (spots: {', '.join(names)})")
    return out


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
    if mech == "act_as":
        out += _act_as_problems(level, lid)
    elif mech == "predict":
        out += _predict_problems(level, lid)
    out += _world_problems(level, lid)
    if mech not in DRAG:
        if not level.get("win"):
            out.append(f"level {lid}: 'win' is needed (what the student made work)")
        if not _rows(level, "item_ids"):
            out.append(f"level {lid}: 'item_ids' is needed (the book items this level makes the student play)")
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


def _act_as_problems(level: dict, lid: str) -> list:
    out = []
    if not str(level.get("role") or "").strip():
        out.append(f"level {lid}: 'role' is needed (who the student is: RBI, the founder, the bank officer ...)")
    if not str(level.get("situation") or "").strip():
        out.append(f"level {lid}: 'situation' is needed (what is happening when the student must decide)")
    choices = level.get("choices")
    if not isinstance(choices, list) or not 2 <= len(choices) <= MAX_CHOICES:
        return out + [f"level {lid}: 2..{MAX_CHOICES} choices are needed (a phone screen)"]
    if not all(isinstance(c, dict) for c in choices):
        return out + [f"level {lid}: every choice must be a JSON object"]
    if not any(c.get("correct") is True for c in choices):
        out.append(f"level {lid}: at least one choice must be correct")
    if all(c.get("correct") is True for c in choices):
        out.append(f"level {lid}: at least one choice must be wrong (a decision needs a wrong way)")
    for i, c in enumerate(choices, 1):
        if not str(c.get("label") or "").strip():
            out.append(f"level {lid}: choice {i} has no label")
        elif len(str(c["label"])) > MAX_LABEL:
            out.append(f"level {lid}: choice {i} label is over {MAX_LABEL} characters (a phone button)")
        if not str(c.get("feedback") or "").strip():
            out.append(f"level {lid}: choice {i} needs 'feedback' ({'what happens' if c.get('correct') else 'what breaks and why'})")
    return out


def _predict_problems(level: dict, lid: str) -> list:
    out = []
    sl = level.get("slider")
    if not isinstance(sl, dict):
        return [f"level {lid}: 'slider' is needed (label, unit, min, max, step, answer, tolerance, predict_prompt, reveal_label)"]
    try:
        lo, hi, step, ans = (float(sl.get(k)) for k in ("min", "max", "step", "answer"))
    except (TypeError, ValueError):
        return [f"level {lid}: slider min, max, step and answer must be numbers"]
    if not (lo < hi and step > 0 and lo <= ans <= hi):
        out.append(f"level {lid}: the slider needs min < max, a step above 0 and the answer inside the range")
    for key in ("label", "predict_prompt", "reveal_label"):
        if not str(sl.get(key) or "").strip():
            out.append(f"level {lid}: slider '{key}' is needed")
    for key in ("feedback_close", "feedback_far"):
        if not str(level.get(key) or "").strip():
            out.append(f"level {lid}: '{key}' is needed (what a close / far guess teaches)")
    return out


def stage_of(level: dict) -> dict:
    """One runtime stage from a valid level (drag, branch or slider engine); ``problems()`` must be empty first."""
    mech = level["mechanic"]
    if mech in ("act_as", "predict"):
        sl = level.get("slider") or {}
        slider = {"label": str(sl.get("label", "")), "unit": str(sl.get("unit", "")), "min": float(sl.get("min", 0)),
                  "max": float(sl.get("max", 0)), "step": float(sl.get("step", 0)), "answer": float(sl.get("answer", 0)),
                  "tolerance": float(sl.get("tolerance") or (float(sl.get("max", 0)) - float(sl.get("min", 0))) * 0.1),
                  "predict_prompt": str(sl.get("predict_prompt", "")), "reveal_label": str(sl.get("reveal_label", "")),
                  "data": list(sl.get("data") or [])} if mech == "predict" else \
            {"label": "", "unit": "", "min": 0, "max": 0, "step": 0, "answer": 0, "tolerance": 0,
             "predict_prompt": "", "reveal_label": "", "data": []}
        situation = (f"{level['role']}: " if level.get("role") else "") + str(level.get("situation", ""))
        return {"stage_id": level["level_id"], "kind": "branch" if mech == "act_as" else "slider",
                "instruction": str(level["instruction"]), "tokens": [], "targets": [], "rules": [], "ordered": False,
                "situation": situation if mech == "act_as" else "",
                "choices": [{"label": str(c["label"]), "correct": c.get("correct") is True, "feedback": str(c["feedback"])}
                            for c in level.get("choices") or []] if mech == "act_as" else [],
                "slider": slider, "feedback_close": str(level.get("feedback_close", "")),
                "feedback_far": str(level.get("feedback_far", "")), "item_ids": list(level.get("item_ids") or [])}
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
        targets = [dict({"id": p["id"], "label": str(p["label"]), "box": {"x": 0, "y": 0, "w": 0, "h": 0}},
                        **({"spot": str(p["spot"])} if p.get("spot") else {})) for p in places]
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
    stage = {"stage_id": level["level_id"], "kind": "drag", "instruction": str(level["instruction"]),
            "tokens": tokens, "targets": targets, "rules": rules, "ordered": bool(ORDERED[mech]),
            "situation": "", "choices": [],
            "slider": {"label": "", "unit": "", "min": 0, "max": 0, "step": 0, "answer": 0, "tolerance": 0,
                       "predict_prompt": "", "reveal_label": "", "data": []},
            "feedback_close": "", "feedback_far": "", "item_ids": list(level.get("item_ids") or [])}
    if isinstance(level.get("world"), dict):
        stage["world"] = dict(level["world"])          # the runtime draws it and puts the places on their spots
    return stage


def mission_of(levels: list, *, title: str, intro: str = "", win_text: str = "") -> dict:
    """One playable mission from levels (each level one stage), for the existing runtime and bot."""
    bad = [p for level in levels for p in problems(level)]
    if bad:
        raise ValueError("levels not playable:\n- " + "\n- ".join(bad))
    return {"mission_id": "-".join(l["level_id"] for l in levels)[:60] or "level", "title": title, "intro": intro,
            "stages": [stage_of(l) for l in levels], "win_text": win_text or levels[-1].get("win", ""),
            "replay_twist": "shuffle_tokens",
            "item_ids": sorted({i for l in levels for i in l.get("item_ids") or []})}
