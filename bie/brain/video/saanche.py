"""Kriya ke saanche: processes built from general motion parts (Task 046 Part D2; the addendum of 2 November 2026).

Navin, on the Money D1 videos: "process show nahi ho rahi hai ... agar wo visuals se clear ho jaise scanner phone scan, tab maja
hai". And on 2 November 2026: "maine salt aur kapde ka example diya ... jis cheej ka jikar hai wohi cheej dikhe; yeh udaharan
maine is rup mein diye the" — examples are illustrations, not a list.

So a saancha is not a drawn scene. It is a composition of general motion parts (``rulebook/saanche.json``): hold, give/take,
move along a path, transform A → B, a screen or sign shows text, a counter or meter changes, appear one by one, refuse/accept,
compare. The actors, the objects (icons the icon index, the asset library or BIE's coder resolved for the things the beat
names) and the numbers come from the beat. A recipe (hand_over, pay_change, barter_swap, upi, card_tap, cheque, coin_count,
refuse, accept, count_stack) is a named composition of parts; template ``compose`` lets the maker write the parts of a process
no recipe has, and a part BIE lacks goes to the missing-capability log. Code checks an action and times it (``compile_action``:
the parts with their frames); the block (``bie/brain/video/blocks/toolbox/saanche.tsx``) draws the parts in a world (C) and on
the canvas (B) alike, and draws no object the plan did not name: an optional object the plan leaves out is a plain chip with
the part's text, or its parts are skipped.
"""
from __future__ import annotations

import json
import re
import zlib
from pathlib import Path

from ..canvas import PlanError

RULEBOOK = json.loads((Path(__file__).resolve().parents[1] / "rulebook" / "saanche.json").read_text(encoding="utf-8"))
VERSION = RULEBOOK["version"]
PARTS = RULEBOOK["parts"]
SPOTS = RULEBOOK["spots"]
RECIPES = RULEBOOK["recipes"]
COMPOSE = "compose"
# role names, object names, amount names (required, then optional) and the steps in the order they happen, per recipe
TEMPLATES = {name: {"roles": tuple(r["roles"]), "objects": tuple(r["objects"]), "optional_objects": dict(r.get("optional_objects") or {}),
                    "amounts": tuple(r["amounts"]), "optional": tuple(r["optional"]), "steps": tuple(r["steps"]),
                    "close": tuple(r["close"]), "says": r["says"]} for name, r in RECIPES.items()}
TEMPLATE_NAMES = tuple(TEMPLATES) + (COMPOSE,)
MOODS = ("neutral", "pleased", "unsure", "refusing")
WHO = ("main", "other")
STYLES = ("tag", "sign", "screen", "ok", "bubble", "write")
SIGNS = ("=", "≠", "?", "vs", "<", ">", "→")
# The stage a template draws on, in its own units: a world places it on the street (x is the stage centre, the bottom on the
# walking line), a canvas fits it into the node's cells. The actors stand about half the stage tall: in a world at zoom 1 that is
# about 310 px of a 1080-px frame (Navin's D2 brief: "an actor in a story piece at least about a quarter of the frame height").
STAGE_W, STAGE_H = 1000, 620
FEET = 600                               # the stage's walking line (saanche.tsx): a world puts it on its street
ACTOR_SHARE = 0.5
MIN_CANVAS_ROWS = 3                      # 3 of 8 rows: an actor about 0.29 of the frame tall, so never a stick figure
COUNT_MAX = 12
PILE_MAX = 18
PLAYED = 12                              # frames of a step's 24-frame motion an action shows before it may fade (15 frames)
CLOSE_AFTER, CLOSE_MAX = 60, 240         # the camera stays close 2 s after the close-up's last step, for at most 8 s in all
NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")
_PROCESS = {k: re.compile(v, re.IGNORECASE) for k, v in RULEBOOK["words"].items() if not k.startswith("_")}
ORDER = tuple(RULEBOOK["order"])
STRONG = tuple(RULEBOOK["strong"])
NUMBER_WORDS = {"एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पाँच": 5, "पांच": 5, "छह": 6, "छः": 6, "सात": 7, "आठ": 8, "नौ": 9, "दस": 10,
                "ग्यारह": 11, "बारह": 12, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
                "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}


def _currency_signs() -> set:
    from . import screen_text                 # lazy: screen_text imports this module lazily too
    return set(screen_text.CURRENCY_SIGNS)


def amount_tokens(text: str) -> list:
    """The amounts a text says, in order and once each: a number with its currency sign before it when it has one ('₹300',
    '$5', '12')."""
    signs = "".join(re.escape(s) for s in _currency_signs())
    found = re.findall(rf"((?:[{signs}]\s?)?\d[\d,]*(?:\.\d+)?)", text or "")
    return list(dict.fromkeys(f.replace(" ", "") for f in found))


def main_look(video_id: str) -> int:
    """The look of a video's one main character (Navin's D2 brief: "one main character per video"): the same face, clothes and
    cap in every part of the video, a different one in the next video."""
    return 3 + zlib.crc32(str(video_id or "video").encode("utf-8")) % 997


def guess_template(say: str) -> str:
    """The recipe a beat's words hint at (the rulebook's words, the strongest first), or ""."""
    for name in ORDER:
        if name in _PROCESS and _PROCESS[name].search(say or ""):
            return name
    return ""


def process_word(name: str, say: str) -> str:
    """The word of a beat that hinted the recipe ``name``."""
    m = _PROCESS[name].search(say or "") if name in _PROCESS else None
    return m.group(0) if m else ""


def parts_text() -> str:
    """The motion parts for the maker's card: name, what it shows, its fields."""
    return "\n".join(f"- {name} ({', '.join(p['needs'] + [o + '?' for o in p.get('optional', [])])}): {p['says']}"
                     for name, p in PARTS.items())


def templates_text() -> str:
    """The recipe list for the maker's card: name, what it shows, steps, roles, objects, amounts, and the parts it is made of."""
    lines = []
    for name, t in TEMPLATES.items():
        r = RECIPES[name]
        bits = [f"steps {', '.join(t['steps'])}"]
        if t["roles"]:
            bits.append(f"actors {', '.join(t['roles'])}")
        objs = list(t["objects"]) + [f"{o} (optional)" for o in t["optional_objects"]]
        if objs:
            bits.append("objects " + ", ".join(objs))
        if t["amounts"] or t["optional"]:
            bits.append("amounts " + ", ".join(list(t["amounts"]) + [f"{a} (optional)" for a in t["optional"]]))
        used = sorted({p["part"] for ps in [r.get("start", [])] + list(r["do"].values()) for p in ps})
        bits.append("parts " + ", ".join(used))
        lines.append(f"- {name}: {t['says']} ({'; '.join(bits)})")
    lines.append(f"- {COMPOSE}: a process no recipe has, written as its parts in order (parts [{{part, cue, ...fields}}]); a part "
                 "BIE lacks: template other in the dikhane ki list, with a note (it goes to the missing-capability log)")
    return "\n".join(lines)


def _numbers(text: str) -> set:
    return {n.replace(",", "") for n in NUMBER.findall(text or "")}


def amount_cue(action: dict, name: str):
    """The cue of the step that first shows an amount: the first step whose parts use it (the narration says the number there)."""
    steps = {s.get("name"): s for s in action.get("steps") or []}
    recipe = RECIPES.get(action.get("template"))
    if recipe:
        for step in recipe["steps"]:
            if any(f"{{{name}" in json.dumps(p, ensure_ascii=False) for p in recipe["do"].get(step, [])):
                return (steps.get(step) or {}).get("cue")
    return ((action.get("steps") or [{}])[0]).get("cue")


def icons_of(action: dict) -> list:
    """The icon ids an action names for its objects."""
    return [o.get("icon") for o in action.get("objects") or [] if o.get("icon")]


def parts_of(action: dict) -> list:
    """The part names an action (planned or compiled) is made of, in order: a recipe's start and step parts, or the maker's own."""
    if action.get("parts") and isinstance(action["parts"][0], dict) and "at" in action["parts"][0]:
        return [p["part"] for p in action["parts"]]                       # compiled
    if action.get("template") == COMPOSE:
        return [p.get("part") for p in action.get("parts") or []]
    r = RECIPES.get(action.get("template"))
    if not r:
        return []
    return [p["part"] for p in r.get("start", [])] + [p["part"] for s in r["steps"] for p in r["do"].get(s, [])]


def _steps_of(action: dict) -> list:
    """The steps of an action: a recipe's own, or one per part of a composed process."""
    if action.get("template") == COMPOSE:
        return [f"p{i + 1}" for i in range(len(action.get("parts") or []))]
    return list(TEMPLATES[action["template"]]["steps"])


def complete_action(action: dict, says: dict) -> list:
    """What code can settle itself before the check (seekh -> BIE, the first Part D2 run of 1 November 2026: 88 rounds for 36
    parts, the maker losing rounds on things the narration already says). In place; returns what was done, for the report:
    - a recipe's one required amount the maker left out is taken from the action's beats when they say exactly one amount; two
      required amounts (a step and a limit) are the smallest and the largest of two or more; a count n is the count the beat says;
    - an amount or step name the recipe does not have is dropped (an object put under amounts, a stray step);
    - a missing last step takes the cue of the step before it (the motion then completes on that word)."""
    name = action.get("template")
    if name not in TEMPLATES:
        return []
    t = TEMPLATES[name]
    aid = action.get("id", "?")
    fixes = []
    allowed = set(t["amounts"]) | set(t["optional"])
    kept = [a for a in action.get("amounts") or [] if a.get("name") in allowed]
    if len(kept) != len(action.get("amounts") or []):
        dropped = [a.get("name") for a in action.get("amounts") or [] if a.get("name") not in allowed]
        fixes.append(f"{aid}: dropped amounts {dropped} that {name} does not have")
        action["amounts"] = kept
    known = set(t["objects"]) | set(t["optional_objects"])
    stray = [o.get("name") for o in action.get("objects") or [] if o.get("name") not in known]
    if stray:                                 # an object the recipe has no place for is not drawn (as before)
        action["objects"] = [o for o in action.get("objects") or [] if o.get("name") in known]
        fixes.append(f"{aid}: dropped objects {stray} that {name} does not have")
    beat_ids = [((s.get("cue") or [None])[0]) for s in action.get("steps") or []]
    text = " ".join(says.get(b, "") for b in dict.fromkeys(beat_ids) if b)
    have = {a.get("name") for a in action.get("amounts") or []}
    def add(amount_name, value):
        action.setdefault("amounts", []).append({"name": amount_name, "text": value})
        fixes.append(f"{aid}: {amount_name} = {value!r} from the narration")
    need = [a for a in t["amounts"] if a not in have and a != "n"]
    with_sign = [a for a in amount_tokens(text) if not a[0].isdigit()] or amount_tokens(text)
    if len(t["amounts"]) == 1 and need and len(with_sign) == 1:
        add(need[0], with_sign[0])
    elif len(t["amounts"]) == 2 and need and len(with_sign) >= 2:
        limit = next((re.sub(r"[{}|].*", "", str(p.get("limit")).strip("{")) for p in _specs({"template": name})
                      if p.get("part") == "meter" and p.get("limit")), None)
        if limit in t["amounts"]:             # the meter's limit is the largest amount said, the other the smallest
            ordered = sorted(with_sign, key=lambda v: float(re.sub(r"[^\d.]", "", v) or 0))
            other = next(a for a in t["amounts"] if a != limit)
            if other in need:
                add(other, ordered[0])
            if limit in need:
                add(limit, ordered[-1])
    if "n" in t["amounts"] and "n" not in have:
        words = [w.strip("।,.!?:;") for w in text.split()]
        counts = [int(w) for w in words if w.isdigit() and 1 <= int(w) <= COUNT_MAX]
        counts += [NUMBER_WORDS[w.lower()] for w in words if w.lower() in NUMBER_WORDS]
        if counts:
            add("n", str(max(counts)))
    steps = action.get("steps") or []
    names = [s.get("name") for s in steps]
    stray = [n for n in names if n not in t["steps"]]
    if stray:
        action["steps"] = [s for s in steps if s.get("name") in t["steps"]]
        fixes.append(f"{aid}: dropped steps {stray} that {name} does not have")
    names = [s.get("name") for s in action.get("steps") or []]
    missing = [n for n in t["steps"] if n not in names]
    if missing == [t["steps"][-1]] and len(t["steps"]) > 1 and action.get("steps"):
        before = next(s for s in action["steps"] if s.get("name") == t["steps"][-2]) if t["steps"][-2] in names else action["steps"][-1]
        action["steps"].append({"name": t["steps"][-1], "cue": list(before.get("cue") or [])})
        fixes.append(f"{aid}: the last step '{t['steps'][-1]}' takes the cue of '{before.get('name')}'")
    return fixes


def _spoken(action: dict, says: dict) -> set:
    cues = [s.get("cue") for s in action.get("steps") or []] + [p.get("cue") for p in action.get("parts") or [] if isinstance(p, dict)]
    beat_ids = [(c or [None])[0] for c in cues]
    return set().union(*[_numbers(says.get(b, "")) for b in beat_ids if b in says]) if beat_ids else set()


def _actor_problems(aid: str, action: dict, roles: tuple | None) -> list:
    out = []
    for a in action.get("actors") or []:
        if roles is not None and a.get("role") not in roles:
            out.append(f"{aid}: {action.get('template')} has no actor '{a.get('role')}' (actors: {', '.join(roles) or 'none'})")
        if a.get("who", "other") not in WHO:
            out.append(f"{aid}: actor 'who' is main or other, not {a.get('who')!r}")
        if a.get("mood", "neutral") not in MOODS:
            out.append(f"{aid}: mood {a.get('mood')!r} is not one of {', '.join(MOODS)}")
    return out


def _compose_problems(aid: str, action: dict, says: dict) -> list:
    """A composed process: every part known, with the fields it needs, referring to the action's own actors and objects, each on
    its cue word; at most two actors on a stage."""
    out = []
    actors = [a.get("role") for a in action.get("actors") or []]
    if len(actors) > 2:
        out.append(f"{aid}: a composed process has at most two actors on its stage, not {len(actors)}")
    out += _actor_problems(aid, action, None)
    objects = {o.get("name"): o for o in action.get("objects") or []}
    parts = action.get("parts") or []
    if not parts:
        out.append(f"{aid}: compose needs its parts in order (parts: {', '.join(PARTS)})")
    spoken = _spoken(action, says)
    for i, p in enumerate(parts):
        name = p.get("part")
        where = f"{aid} part {i + 1}"
        if name not in PARTS:
            out.append(f"{where}: {name!r} is not a motion part BIE draws ({', '.join(PARTS)}); a missing part goes to the "
                       "missing-capability log: template other in the dikhane ki list, with a note")
            continue
        if not p.get("cue"):
            out.append(f"{where}: {name} needs its cue word")
        for field in PARTS[name]["needs"]:
            value = p.get(field)
            if value in (None, "", []):
                out.append(f"{where}: {name} needs {field}")
                continue
            if field in ("actor", "from"):
                if value not in actors:
                    out.append(f"{where}: {field} {value!r} is not one of the actors ({', '.join(actors) or 'none'})")
            elif field in ("object", "into", "left", "right"):
                if not (objects.get(value) or {}).get("icon"):
                    out.append(f"{where}: {field} {value!r} is not one of the objects with an icon ({', '.join(objects) or 'none'})")
            elif field in ("to", "on") and name != "meter":
                if value not in actors and not (objects.get(value) or {}).get("icon") and value not in SPOTS:
                    out.append(f"{where}: {field} {value!r} is not an actor, an object or a spot ({', '.join(SPOTS)})")
        if p.get("style") and p["style"] not in STYLES:
            out.append(f"{where}: style {p['style']!r} is not one of {', '.join(STYLES)}")
        if p.get("sign") and p["sign"] not in SIGNS:
            out.append(f"{where}: sign {p['sign']!r} is not one of {' '.join(SIGNS)}")
        if p.get("n") not in (None, "", 0) and not (str(p["n"]).isdigit() and 1 <= int(p["n"]) <= COUNT_MAX):
            out.append(f"{where}: n is a whole number from 1 to {COUNT_MAX}")
        for key in ("text", "left_text", "right_text", "from_text", "to_text"):
            missing = [n for n in _numbers(str(p.get(key) or "")) if n not in spoken]
            if missing:
                out.append(f"{where}: the number in {p.get(key)!r} is not said in the action's beats (CV-16)")
    return out


def problems_of(action: dict, says: dict) -> list:
    """What is wrong with an action before it is timed: the recipe (or the composed parts), its actors, objects, amounts and
    steps (each amount a number said in the narration of one of the action's beats, CV-16)."""
    aid = action.get("id", "?")
    name = action.get("template")
    if name == COMPOSE:
        return _compose_problems(aid, action, says)
    if name not in TEMPLATES:
        return [f"{aid}: template {name!r} is not a recipe ({', '.join(TEMPLATE_NAMES)}); a process no recipe has is composed "
                "from the motion parts (template compose)"]
    t = TEMPLATES[name]
    out = []
    roles = {a.get("role") for a in action.get("actors") or []}
    for r in t["roles"]:
        if r not in roles:
            out.append(f"{aid}: {name} needs the actor '{r}'")
    out += _actor_problems(aid, action, t["roles"])
    objects = {o.get("name"): o for o in action.get("objects") or []}
    for o in t["objects"]:
        if not (objects.get(o) or {}).get("icon"):
            out.append(f"{aid}: {name} needs the object '{o}' with an icon (the thing the story names, from the icon candidates)")
    amounts = {a.get("name"): str(a.get("text") or "") for a in action.get("amounts") or []}
    for a in t["amounts"]:
        if not amounts.get(a):
            out.append(f"{aid}: {name} needs the amount '{a}' (the number goes on what carries it: a tag, a screen, a meter)")
    spoken = _spoken(action, says)
    for a, text in amounts.items():
        if a not in t["amounts"] + t["optional"]:
            out.append(f"{aid}: {name} has no amount '{a}'")
            continue
        if a == "n":                          # n is how many things appear (like a crowd's n), not a number written on screen
            if not text.strip().isdigit() or not 1 <= int(text) <= COUNT_MAX:
                out.append(f"{aid}: {name}'s n is a whole number from 1 to {COUNT_MAX}, not {text!r}")
            continue
        missing = [n for n in _numbers(text) if n not in spoken]
        if missing:
            out.append(f"{aid}: the amount {text!r} is not said in the action's beats; write numbers the way the narration says them (CV-16)")
    for row in action.get("texts") or []:
        missing = [n for n in _numbers(str(row.get("text") or "")) if n not in spoken]
        if missing:
            out.append(f"{aid}: the text {row.get('text')!r} has a number not said in the action's beats (CV-16)")
        if row.get("step") not in t["steps"]:
            out.append(f"{aid}: a text belongs to one of the steps ({', '.join(t['steps'])}), not {row.get('step')!r}")
    steps = {s.get("name"): s for s in action.get("steps") or []}
    for s in t["steps"]:
        if s not in steps:
            out.append(f"{aid}: {name} needs the step '{s}' with its cue word")
    for s in steps:
        if s not in t["steps"]:
            out.append(f"{aid}: {name} has no step '{s}' (steps: {', '.join(t['steps'])})")
    return out


# ---------------------------------------------------------------- timing the parts

def _fill(text, amounts: dict, labels: dict) -> str:
    """'{amount}' → the amount; '{x|fallback}' → x's amount or the fallback (itself filled); '{label:role}' → the actor's label."""
    if not isinstance(text, str):
        return text
    def one(m):
        body = m.group(1)
        if body.startswith("label:"):
            return labels.get(body[6:], "") or body[6:]
        key, _, fallback = body.partition("|")
        if amounts.get(key):
            return amounts[key]
        return _fill(fallback, amounts, labels) if fallback else ""
    out, prev = text, None
    while out != prev:
        prev = out
        out = re.sub(r"\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", one, out, count=1)
    return out.strip()


def _beat_end(cue, beat_spans: dict | None, start: int, n: int) -> int:
    bid = (cue or [None])[0]
    span = (beat_spans or {}).get(bid)
    return (span[0] + span[1]) if span else start + n * 12


def compile_action(action: dict, frame_of, says: dict, *, icon_paths: dict | None = None, main_look: int = 7,
                   beat_spans: dict | None = None) -> dict:
    """The block's data for one action: the motion parts with their frames (``parts``), the step frames in order
    (``step_at``), the actors with their looks (the video's one main character keeps the same look in every part), the objects
    with their image sources (a chip with text for an optional object the plan leaves out), the amounts, and the close-up span.
    ``beat_spans`` maps a beat id to its (start, length) in frames, so things that appear one by one spread over their beat."""
    fixes = complete_action(action, says)
    bad = problems_of(action, says)
    if bad:
        raise PlanError("; ".join(bad))
    name = action["template"]
    aid = action.get("id", "?")
    if name == COMPOSE:
        roles = tuple(a["role"] for a in action.get("actors") or [])
        step_names = _steps_of(action)
        cues = {f"p{i + 1}": p["cue"] for i, p in enumerate(action["parts"])}
        recipe = {"start": [], "do": {f"p{i + 1}": [{k: v for k, v in p.items() if k != "cue" and v not in (None, "", [], False, 0)}]
                                       for i, p in enumerate(action["parts"])},
                  "close": []}
        optional = {}
        required_objects = tuple(o["name"] for o in action.get("objects") or [])
    else:
        t = TEMPLATES[name]
        roles, step_names, recipe, optional, required_objects = t["roles"], list(t["steps"]), RECIPES[name], t["optional_objects"], t["objects"]
        cues = {s["name"]: s["cue"] for s in action["steps"]}
    frames = {s: frame_of(cues[s]) for s in step_names}
    order = [frames[s] for s in step_names]
    if order != sorted(order):            # the cue words come in another order: the motion still follows the recipe, on them
        order = sorted(order)
        frames = dict(zip(step_names, order))
        fixes.append(f"{aid}: the steps of {name} follow its order ({', '.join(step_names)}) on its cue words in time order")
    others = 0
    actors, slot, labels = [], {}, {}
    for role in roles:
        a = next(x for x in action["actors"] if x["role"] == role)
        if a.get("who", "other") == "main":
            look = main_look
        else:
            others += 1
            look = main_look * 31 + others * 7
        slot[role] = len(actors)
        labels[role] = str(a.get("label") or "")[:18]
        actors.append({"role": role, "look": look, "mood": a.get("mood", "neutral"), "label": labels[role],
                       "main": a.get("who", "other") == "main"})
    amounts = {a["name"]: str(a["text"]) for a in action.get("amounts") or []}
    extra = {row["step"]: str(row["text"]) for row in action.get("texts") or [] if row.get("step") and row.get("text")}
    objects = {}
    for o in action.get("objects") or []:
        if o.get("icon") and (o.get("name") in required_objects or o.get("name") in optional):
            objects[o["name"]] = {"src": (icon_paths or {}).get(o["icon"], o["icon"]), "icon": o["icon"], "label": str(o.get("label") or "")[:18]}
    at0 = max(0, order[0] - 18)
    parts = []

    def target(value):
        """A part's target: the first of the names given that is present (an actor, an object, a spot)."""
        for v in (value if isinstance(value, list) else [value]):
            if v in slot:
                return {"actor": slot[v]}
            if v in objects:
                return {"object": v}
            if v in SPOTS:
                return {"spot": v}
        return None

    obj_keys = {"hold": ("object",), "give": ("object",), "move": ("object",), "transform": ("object", "into"),
                "show_text": ("inside",), "appear": ("object",), "refuse": ("object",), "accept": ("object",),
                "compare": ("left", "right"), "meter": ()}

    def add_part(spec: dict, at: int, step: str | None):
        if spec.get("if") and not amounts.get(spec["if"]):
            return
        kind = spec["part"]
        p = {"part": kind, "at": at}
        text = _fill(spec["text"], amounts, labels) if isinstance(spec.get("text"), str) else None
        if kind == "show_text" and step and extra.get(step):
            text = f"{text} {extra[step]}".strip() if text else extra[step]
        for key in obj_keys.get(kind, ()):
            ref = spec.get(key)
            if ref in (None, ""):
                continue
            if ref not in objects:
                if optional.get(ref) == "chip":
                    objects[ref] = {"chip": text or "", "label": ""}
                elif key == "inside":
                    continue
                else:
                    return                    # an optional object the plan left out: its part is skipped
            p[key] = ref
        if kind != "meter":
            for key in ("actor", "from"):
                if spec.get(key) in (None, ""):
                    continue
                if spec[key] not in slot:
                    if key == "actor" and kind in ("refuse", "accept"):
                        continue              # the mark lands without a person
                    return
                p[key] = slot[spec[key]]
            if spec.get("to") not in (None, ""):
                if kind == "give":
                    if spec["to"] not in slot:
                        return
                    p["to"] = slot[spec["to"]]
                else:
                    tgt = target(spec["to"])
                    if tgt is None:
                        return
                    p["to"] = tgt
        if spec.get("on") not in (None, ""):
            tgt = target(spec["on"])
            if tgt is None:
                return
            p["on"] = tgt
        if kind == "move" and spec.get("into") is True:
            p["into_target"] = True
        for key in ("reach", "back", "style", "layout", "dir", "sign", "spot"):
            if spec.get(key) not in (None, "", False):
                p[key] = spec[key]
        for key in ("title", "left_text", "right_text", "limit"):
            if isinstance(spec.get(key), str) and spec[key]:
                p[key] = _fill(spec[key], amounts, labels)
        if kind == "meter":
            p["value_from"] = _fill(str(spec.get("from") or ""), amounts, labels)
            p["value_to"] = _fill(str(spec.get("to") or ""), amounts, labels)
            p.setdefault("style", "bar")
        if text is not None:
            p["text"] = text
        if spec.get("end"):
            p["end"] = frames.get(spec["end"], at + 60)
        if kind == "appear":
            n = spec.get("n")
            n = _fill(n, amounts, labels) if isinstance(n, str) else n
            n = max(1, min(COUNT_MAX, int(n or 1)))
            if spec.get("layout") == "pile":
                end = p.get("end", at + 6 * PILE_MAX)
                p["items"] = [at + 6 * i for i in range(max(1, min(PILE_MAX, (end - at) // 6)))]
            elif n > 1:
                end = _beat_end(cues.get(step) if step else None, beat_spans, at, n)
                gap = max(6, (end - at) // n)
                p["items"] = [at + i * gap for i in range(n)]
            else:
                p["items"] = [at]
        parts.append(p)

    for spec in recipe.get("start", []):
        add_part(spec, at0, None)
    for step in step_names:
        for spec in recipe["do"].get(step, []):
            add_part(spec, frames[step], step)
    for i, p in enumerate(parts):          # a sign shows until the next sign on the same target replaces it
        if p["part"] == "show_text":
            nxt = next((q for q in parts[i + 1:] if q["part"] == "show_text" and q.get("on") == p.get("on")), None)
            if nxt:
                p["until"] = nxt["at"]
    out = {"id": action["id"], "kind": "action", "template": name, "step_at": frames, "actors": actors,
           "objects": objects, "amounts": amounts, "parts": parts, "at": at0}
    grid = next((p for p in parts if p["part"] == "appear" and p.get("layout") == "grid"), None)
    if grid:
        out["items"] = list(grid["items"])
    if action.get("until_cue"):
        out["until"] = frame_of(action["until_cue"])
        fit_items(out, out["until"])                  # code spread the items; they finish before the action leaves
        last = last_moment(out)
        if out["until"] < last + PLAYED:          # seekh -> BIE: an until on the last step's own word hid that step
            out["until"] = last + PLAYED
            fixes.append(f"{aid}: stays until its last step has played ({PLAYED} frames after it)")
    close = recipe.get("close") or ([step_names[0], step_names[-1]] if name == COMPOSE and len(step_names) > 1 else [])
    if action.get("close_up", True) and close:
        first, last = (frames[s] for s in close)
        if last + CLOSE_AFTER - first > CLOSE_MAX:        # a long gap between the steps: the camera stays close on the last one
            first = last
        out["close_up"] = {"at": max(0, first - 10), "until": last + CLOSE_AFTER, "step": close[-1]}
    if fixes:
        out["auto_fixes"] = fixes
    return out


ITEM_GAP_MIN = 3


def fit_items(action: dict, end: int) -> bool:
    """Things that appear one by one (spread by code over the rest of their beat) are brought closer so the last one has played
    by ``end`` (seekh -> BIE, the first Part D2 run: a stack of 10 left after 6 had appeared, so the count on screen was wrong).
    True when they fit (at least ITEM_GAP_MIN frames apart), or there is nothing to fit."""
    items = action.get("items") or []
    if not items or items[-1] + PLAYED <= end:
        return True
    if len(items) == 1:
        return items[0] + PLAYED <= end
    gap = (end - PLAYED - items[0]) // (len(items) - 1)
    if gap < ITEM_GAP_MIN:
        return False
    action["items"] = [items[0] + i * gap for i in range(len(items))]
    for p in action.get("parts") or []:
        if p.get("part") == "appear" and p.get("layout") == "grid":
            p["items"] = list(action["items"])
    return True


def last_moment(action: dict) -> int | None:
    """The frame of an action's last step or counted item."""
    marks = list((action.get("step_at") or {}).values()) + list(action.get("items") or [])
    return max(marks) if marks else None


def _specs(action: dict) -> list:
    """The parts of an action as dicts: compiled parts, a composed process's own, or a recipe's (start and step parts)."""
    if action.get("parts") and isinstance(action["parts"][0], dict):
        return list(action["parts"])
    r = RECIPES.get(action.get("template")) or {}
    return list(r.get("start", [])) + [p for s in r.get("steps", []) for p in r.get("do", {}).get(s, [])]


def realises(action: dict) -> set:
    """The relations an action shows, read from the parts it is made of by the rules of ``rulebook/saanche.json`` ("realises"):
    a relation holds when any of its conditions does (and the action has its ``min_parts``)."""
    specs = _specs(action)
    names = [p.get("part") for p in specs]
    amounts = {a.get("name"): str(a.get("text") or "") for a in action.get("amounts") or []}
    def appear_n():
        best = 0
        for p in specs:
            if p.get("part") != "appear":
                continue
            if p.get("layout") == "pile" or len(p.get("items") or []) > 1:
                return COUNT_MAX
            n = p.get("n")
            n = _fill(n, amounts, {}) if isinstance(n, str) else n
            try:
                best = max(best, int(n or 1))
            except (TypeError, ValueError):
                best = max(best, 1)
        return best
    out = set()
    for rel, rule in RULEBOOK["realises"].items():
        if len(names) < rule.get("min_parts", 0):
            continue
        conds = []
        if "any" in rule:
            conds.append(any(n in rule["any"] for n in names))
        if "all_of" in rule:
            conds.append(all(n in names for n in rule["all_of"]))
        if "gives_min" in rule:
            conds.append(names.count("give") >= rule["gives_min"])
        if "meter_with" in rule:
            conds.append(any(p.get("part") == "meter" and p.get(rule["meter_with"]) for p in specs))
        if "meter_style" in rule:
            conds.append(any(p.get("part") == "meter" and p.get("style") == rule["meter_style"] for p in specs))
        if "give_with_text" in rule:
            conds.append(any(p.get("part") == "give" and p.get("text") for p in specs))
        if "appear_n_min" in rule:
            conds.append(appear_n() >= rule["appear_n_min"])
        if not conds:
            conds.append(True)                # min_parts alone
        if any(conds):
            out.add(rel)
    return out


def action_beats(action: dict) -> set:
    """The beat ids an action's steps (or composed parts) are cued in."""
    cues = [s.get("cue") for s in action.get("steps") or []] + [p.get("cue") for p in action.get("parts") or [] if isinstance(p, dict) and "cue" in p]
    return {(c or [None])[0] for c in cues} - {None}


def top_of(action: dict) -> int:
    """Where an action's drawing starts above its stage (stage units from the stage top), from the parts it is made of."""
    tops = RULEBOOK["top"]
    names = set(parts_of(action))
    return min([tops.get(n, tops["default"]) for n in names] or [tops["default"]])
