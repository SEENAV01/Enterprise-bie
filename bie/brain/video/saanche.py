"""Kriya ke saanche: process templates (Task 046 Part D2, Navin's verdict of 1 November 2026).

Navin, on the Money D1 videos: "process show nahi ho rahi hai, like upi payment ka jikar hai shop par, par agar wo visuals se
clear ho jaise scanner phone scan, tab maja hai" and "mera meaning hai ki visuals dekhkar concept clear ho aur user narration
se connect kar sake". A world showed a place, people and boards, but nothing that happens.

A saancha is a reusable, parameterised action with actors, objects, amounts and cue words: the maker names the template, who
does it, with what and for how much, and the word of each step; this code checks it and times it, and the block draws it
(``bie/brain/video/blocks/toolbox/saanche.tsx``) in a world (C) and on the canvas (B) alike, with the camera moving in to
the action (hands, the phone screen, the passbook) and back out. The first set (Navin's list):

- ``hand_over``     A gives a thing to B (steps: give, take)
- ``pay_change``    pay with a note and get change back: ₹500 in, the goods out, ₹200 back (pay, goods, change)
- ``barter_swap``   two people swap their things, with the "do they both want it?" moment (offer, ask, swap)
- ``upi``           a QR stand at the shop, the phone scans, the phone says "₹300 paid", the shopkeeper's says "received"
                    (scan, paid, received)
- ``card_tap``      a card taps a POS machine, the machine approves (tap, approved)
- ``cheque``        written, handed to the bank, the two balances change (write, hand, balances)
- ``coin_count``    coins counted onto a pile next to a limit meter that stops at its red line (count, limit)
- ``refuse``        a head shake and a cross on the thing (show, refuse)
- ``accept``        a nod and a tick on the thing (show, accept)
- ``count_stack``   n things appear one by one as they are said (count)

Numbers go onto the objects (the note shows ₹500, the phone screen ₹300, the passbook its balance), never onto a board, and
every amount must be said in the narration (CV-16). A process the set lacks goes to the missing-capability log with its
beats (``bie/brain/canvas_director.py``).
"""
from __future__ import annotations

import re

import zlib

from ..canvas import PlanError

# role names, object names, amount names (required, then optional) and the steps in the order they happen
TEMPLATES = {
    "hand_over": {"roles": ("giver", "taker"), "objects": ("thing",), "amounts": (), "optional": (), "steps": ("give", "take"),
                  "close": ("give", "take"), "says": "A gives a thing to B"},
    "pay_change": {"roles": ("buyer", "seller"), "objects": ("goods",), "amounts": ("paid", "change"), "optional": ("price",),
                   "steps": ("pay", "goods", "change"), "close": ("pay", "change"),
                   "says": "the buyer pays a note, takes the goods and gets the change back (₹500 in, ₹200 back)"},
    "barter_swap": {"roles": ("a", "b"), "objects": ("a_thing", "b_thing"), "amounts": (), "optional": (),
                    "steps": ("offer", "ask", "swap"), "close": ("ask", "swap"),
                    "says": "two people swap their things; at 'ask' both wonder whether they want the other's thing"},
    "upi": {"roles": ("buyer", "seller"), "objects": (), "amounts": ("amount",), "optional": (), "steps": ("scan", "paid", "received"),
            "close": ("scan", "paid"), "says": "the buyer's phone scans the shop's QR stand; the phone shows '₹300 paid', the shopkeeper's 'received'"},
    "card_tap": {"roles": ("buyer", "seller"), "objects": (), "amounts": ("amount",), "optional": (), "steps": ("tap", "approved"),
                 "close": ("tap", "approved"), "says": "a card taps the shop's POS machine; the machine shows the amount approved"},
    "cheque": {"roles": ("payer", "payee"), "objects": (), "amounts": ("amount",),
               "optional": ("payer_before", "payer_after", "payee_before", "payee_after"),
               "steps": ("write", "hand", "balances"), "close": ("write", "hand"),
               "says": "a cheque is written for the amount, handed to the bank, and the two passbooks change (payer down, payee up)"},
    "coin_count": {"roles": (), "objects": ("coin",), "amounts": ("each", "limit"), "optional": (), "steps": ("count", "limit"),
                   "close": ("limit", "limit"), "says": "coins drop onto a pile while a meter rises; at 'limit' it stops at its red line"},
    "refuse": {"roles": ("who",), "objects": ("thing",), "amounts": (), "optional": (), "steps": ("show", "refuse"), "close": ("refuse", "refuse"),
               "says": "the person looks at the thing, shakes the head, and a cross lands on the thing"},
    "accept": {"roles": ("who",), "objects": ("thing",), "amounts": (), "optional": (), "steps": ("show", "accept"), "close": ("accept", "accept"),
               "says": "the person looks at the thing, nods, and a tick lands on the thing"},
    "count_stack": {"roles": (), "objects": ("thing",), "amounts": ("n",), "optional": (), "steps": ("count",), "close": (),
                    "says": "n things appear one by one as they are said"},
}
# the step that first shows each amount (its number is said in that step's beat: the screen-text check reads it there)
AMOUNT_STEP = {"paid": "pay", "change": "change", "price": "pay", "amount": None, "each": "count", "limit": "limit",
               "payer_before": "balances", "payer_after": "balances", "payee_before": "balances", "payee_after": "balances", "n": "count"}
AMOUNT_STEP_OF = {"upi": {"amount": "scan"}, "card_tap": {"amount": "tap"}, "cheque": {"amount": "write"}}
MOODS = ("neutral", "pleased", "unsure", "refusing")
WHO = ("main", "other")
# The stage a template draws on, in its own units: a world places it on the street (x is the stage centre, the bottom on the
# walking line), a canvas fits it into the node's cells. The actors stand about half the stage tall: in a world at zoom 1 that is
# about 310 px of a 1080-px frame (Navin's D2 brief: "an actor in a story piece at least about a quarter of the frame height").
STAGE_W, STAGE_H = 1000, 620
FEET = 600                               # the stage's walking line (saanche.tsx): a world puts it on its street
ACTOR_SHARE = 0.5
MIN_CANVAS_ROWS = 3                      # 3 of 8 rows: an actor about 0.29 of the frame tall, so never a stick figure
COUNT_MAX = 12
PLAYED = 12                              # frames of a step's 24-frame motion an action shows before it may fade (15 frames)
CLOSE_AFTER, CLOSE_MAX = 60, 240         # the camera stays close 2 s after the close-up's last step, for at most 8 s in all
NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")
# words that name a process in a beat (Hindi, Hinglish and English), so code can suggest the template to the maker
PROCESS_WORDS = {
    "upi": r"\bupi\b|\bqr\b|स्कैन|scan|scanner|स्कैनर|bhim|phonepe|paytm|gpay|google pay|क्यूआर",
    "card_tap": r"\bcard\b|कार्ड|\bpos\b|swipe|tap|टैप|debit card|credit card|rupay",
    "cheque": r"cheque|check book|चेक|चैक",
    "pay_change": r"वापस|लौटा|change|चिल्लर|छुट्टा|खुल्ले|बाकी पैसे|बचे पैसे|balance return",
    "barter_swap": r"barter|अदला-बदली|अदला बदली|बदले में|के बदले|swap|exchange of goods|वस्तु विनिमय",
    "coin_count": r"सीमा|limit|ceiling|अधिकतम|तक ही",
    "count_stack": r"गिन|count|एक-एक|एक एक करके|one by one",
    "refuse": r"मना|इनकार|refuse|reject|नहीं लेगा|नहीं लेता|नहीं लेती|नहीं चलेगा|मान्य नहीं|legal tender नहीं",
    "accept": r"स्वीकार|accept|मान लेता|ले लेता|ले लेती|मंज़ूर|मंजूर",
    "hand_over": r"दिया|देता|देती|दे दिया|थमा|हाथ में|hands? over|gives?\b",
}
_PROCESS = {k: re.compile(v, re.IGNORECASE) for k, v in PROCESS_WORDS.items()}
ORDER = ("upi", "card_tap", "cheque", "pay_change", "barter_swap", "coin_count", "refuse", "accept", "count_stack", "hand_over")


def main_look(video_id: str) -> int:
    """The look of a video's one main character (Navin's D2 brief: "one main character per video"): the same face, clothes and
    cap in every part of the video, a different one in the next video."""
    return 3 + zlib.crc32(str(video_id or "video").encode("utf-8")) % 997


def guess_template(say: str) -> str:
    """The template a beat's words name, or "" (the strongest process first: UPI before card before cheque before change)."""
    for name in ORDER:
        if _PROCESS[name].search(say or ""):
            return name
    return ""


def templates_text() -> str:
    """The template list for the maker's card: name, steps, roles, objects, amounts and what it shows."""
    lines = []
    for name, t in TEMPLATES.items():
        parts = [f"steps {', '.join(t['steps'])}"]
        if t["roles"]:
            parts.append(f"actors {', '.join(t['roles'])}")
        if t["objects"]:
            parts.append(f"objects {', '.join(t['objects'])}")
        if t["amounts"] or t["optional"]:
            parts.append("amounts " + ", ".join(list(t["amounts"]) + [f"{a} (optional)" for a in t["optional"]]))
        lines.append(f"- {name}: {t['says']} ({'; '.join(parts)})")
    return "\n".join(lines)


def _numbers(text: str) -> set:
    return {n.replace(",", "") for n in NUMBER.findall(text or "")}


def amount_cue(action: dict, name: str):
    """The cue of the step that first shows an amount (the narration says the number in that step's beat)."""
    step = AMOUNT_STEP_OF.get(action.get("template"), {}).get(name) or AMOUNT_STEP.get(name)
    steps = {s.get("name"): s for s in action.get("steps") or []}
    return (steps.get(step) or (action.get("steps") or [{}])[0]).get("cue")


def icons_of(action: dict) -> list:
    """The icon ids an action names for its objects."""
    return [o.get("icon") for o in action.get("objects") or [] if o.get("icon")]


RUPEE_NUMBER = re.compile(r"₹\s?(\d[\d,]*(?:\.\d+)?)")
NUMBER_WORDS = {"एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पाँच": 5, "पांच": 5, "छह": 6, "छः": 6, "सात": 7, "आठ": 8, "नौ": 9, "दस": 10,
                "ग्यारह": 11, "बारह": 12, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
                "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}


def complete_action(action: dict, says: dict) -> list:
    """What code can settle itself before the check (seekh -> BIE, the first Part D2 run of 1 November 2026: 88 rounds for 36
    parts, the maker losing rounds on things the narration already says). In place; returns what was done, for the report:
    - an amount the template needs and the maker left out is taken from the action's beats when they say exactly one rupee
      amount (upi, card_tap, cheque), the smallest and the largest of two or more (coin_count's each and limit), or a count
      (count_stack's n);
    - an amount or step name the template does not have is dropped (an object put under amounts, a stray step);
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
    beat_ids = [((s.get("cue") or [None])[0]) for s in action.get("steps") or []]
    text = " ".join(says.get(b, "") for b in dict.fromkeys(beat_ids) if b)
    have = {a.get("name") for a in action.get("amounts") or []}
    rupees = list(dict.fromkeys(RUPEE_NUMBER.findall(text)))
    def add(amount_name, value):
        action.setdefault("amounts", []).append({"name": amount_name, "text": value})
        fixes.append(f"{aid}: {amount_name} = {value!r} from the narration")
    if name in ("upi", "card_tap", "cheque") and "amount" not in have and len(rupees) == 1:
        add("amount", f"₹{rupees[0]}")
    if name == "coin_count" and len(rupees) >= 2:       # one amount alone could be either: the maker names it
        values = sorted(rupees, key=lambda r: float(r.replace(",", "")))
        if "each" not in have:
            add("each", f"₹{values[0]}")
        if "limit" not in have and len(values) >= 2:
            add("limit", f"₹{values[-1]}")
    if name == "count_stack" and "n" not in have:
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


def problems_of(action: dict, says: dict) -> list:
    """What is wrong with an action before it is timed: the template, its actors, objects, amounts and steps (each amount a
    number said in the narration of one of the action's beats, CV-16)."""
    aid = action.get("id", "?")
    name = action.get("template")
    if name not in TEMPLATES:
        return [f"{aid}: template {name!r} is not a saancha ({', '.join(TEMPLATES)}); a process the set lacks goes to the "
                "missing-capability log: draw it with icons and arrows meanwhile"]
    t = TEMPLATES[name]
    out = []
    roles = {a.get("role") for a in action.get("actors") or []}
    for r in t["roles"]:
        if r not in roles:
            out.append(f"{aid}: {name} needs the actor '{r}'")
    for a in action.get("actors") or []:
        if a.get("role") not in t["roles"]:
            out.append(f"{aid}: {name} has no actor '{a.get('role')}' (actors: {', '.join(t['roles']) or 'none'})")
        if a.get("who", "other") not in WHO:
            out.append(f"{aid}: actor 'who' is main or other, not {a.get('who')!r}")
        if a.get("mood", "neutral") not in MOODS:
            out.append(f"{aid}: mood {a.get('mood')!r} is not one of {', '.join(MOODS)}")
    objects = {o.get("name"): o for o in action.get("objects") or []}
    for o in t["objects"]:
        if not (objects.get(o) or {}).get("icon"):
            out.append(f"{aid}: {name} needs the object '{o}' with an icon (the thing the story names, from the icon candidates)")
    amounts = {a.get("name"): str(a.get("text") or "") for a in action.get("amounts") or []}
    for a in t["amounts"]:
        if not amounts.get(a):
            out.append(f"{aid}: {name} needs the amount '{a}' (the number goes on the object: the note, the screen, the passbook)")
    beat_ids = [((s.get("cue") or [None])[0]) for s in action.get("steps") or []]
    spoken = set().union(*[_numbers(says.get(b, "")) for b in beat_ids if b in says]) if beat_ids else set()
    for a, text in amounts.items():
        if a not in t["amounts"] + t["optional"]:
            out.append(f"{aid}: {name} has no amount '{a}'")
            continue
        if name == "count_stack":            # n is how many things appear (like a crowd's n), not a number written on screen
            if not text.strip().isdigit() or not 1 <= int(text) <= COUNT_MAX:
                out.append(f"{aid}: count_stack's n is a whole number from 1 to {COUNT_MAX}, not {text!r}")
            continue
        missing = [n for n in _numbers(text) if n not in spoken]
        if missing:
            out.append(f"{aid}: the amount {text!r} is not said in the action's beats; write numbers the way the narration says them (CV-16)")
    steps = {s.get("name"): s for s in action.get("steps") or []}
    for s in t["steps"]:
        if s not in steps:
            out.append(f"{aid}: {name} needs the step '{s}' with its cue word")
    for s in steps:
        if s not in t["steps"]:
            out.append(f"{aid}: {name} has no step '{s}' (steps: {', '.join(t['steps'])})")
    return out


def compile_action(action: dict, frame_of, says: dict, *, icon_paths: dict | None = None, main_look: int = 7,
                   beat_spans: dict | None = None) -> dict:
    """The block's data for one action: step frames in order (``step_at``, so the compilers' step lists stay lists), actors
    with their looks (the video's one main character keeps the same look in every part), objects with their image sources,
    amounts, and the close-up span. ``beat_spans`` maps a beat id to its (start, length) in frames, so count_stack spreads
    its items over the rest of its beat."""
    fixes = complete_action(action, says)
    bad = problems_of(action, says)
    if bad:
        raise PlanError("; ".join(bad))
    t = TEMPLATES[action["template"]]
    steps = {s["name"]: s for s in action["steps"]}
    frames = {}
    for name in t["steps"]:
        frames[name] = frame_of(steps[name]["cue"])
    order = [frames[n] for n in t["steps"]]
    if order != sorted(order):            # the cue words come in another order: the motion still follows the template, on them
        order = sorted(order)
        frames = dict(zip(t["steps"], order))
        fixes.append(f"{action.get('id', '?')}: the steps of {action['template']} follow the template ({', '.join(t['steps'])}) on its cue words in time order")
    others = 0
    actors = []
    for role in t["roles"]:
        a = next(x for x in action["actors"] if x["role"] == role)
        if a.get("who", "other") == "main":
            look = main_look
        else:
            others += 1
            look = main_look * 31 + others * 7
        actors.append({"role": role, "look": look, "mood": a.get("mood", "neutral"), "label": str(a.get("label") or "")[:18],
                       "main": a.get("who", "other") == "main"})
    objects = {}
    for o in action.get("objects") or []:
        if o.get("name") in t["objects"]:
            objects[o["name"]] = {"src": (icon_paths or {}).get(o["icon"], o["icon"]), "icon": o["icon"], "label": str(o.get("label") or "")[:18]}
    amounts = {a["name"]: str(a["text"]) for a in action.get("amounts") or [] if a.get("name") in t["amounts"] + t["optional"]}
    out = {"id": action["id"], "kind": "action", "template": action["template"], "step_at": frames, "actors": actors,
           "objects": objects, "amounts": amounts, "at": max(0, order[0] - 18)}
    if action["template"] == "count_stack":
        n = int(amounts["n"])
        start = frames["count"]
        bid = steps["count"]["cue"][0]
        span = (beat_spans or {}).get(bid)
        end = (span[0] + span[1]) if span else start + n * 12
        gap = max(6, (end - start) // max(1, n))
        out["items"] = [start + i * gap for i in range(n)]
    if action.get("until_cue"):
        out["until"] = frame_of(action["until_cue"])
        fit_items(out, out["until"])                  # code spread the items; they finish before the action leaves
        last = max(list(frames.values()) + out.get("items", []))
        if out["until"] < last + PLAYED:          # seekh -> BIE: an until on the last step's own word hid that step
            out["until"] = last + PLAYED
            fixes.append(f"{action.get('id', '?')}: stays until its last step has played ({PLAYED} frames after it)")
    if action.get("close_up", True) and t["close"]:
        first, last = (frames[s] for s in t["close"])
        if last + CLOSE_AFTER - first > CLOSE_MAX:        # a long gap between the steps: the camera stays close on the last one
            first = last
        out["close_up"] = {"at": max(0, first - 10), "until": last + CLOSE_AFTER, "step": t["close"][-1]}
    if fixes:
        out["auto_fixes"] = fixes
    return out


ITEM_GAP_MIN = 3


def fit_items(action: dict, end: int) -> bool:
    """count_stack's items (spread by code over the rest of the beat) are brought closer so the last one has played by ``end``
    (seekh -> BIE, the first Part D2 run: a stack of 10 left after 6 had appeared, so the count on screen was wrong). True when
    they fit (at least ITEM_GAP_MIN frames apart), or there is nothing to fit."""
    items = action.get("items") or []
    if not items or items[-1] + PLAYED <= end:
        return True
    if len(items) == 1:
        return items[0] + PLAYED <= end
    gap = (end - PLAYED - items[0]) // (len(items) - 1)
    if gap < ITEM_GAP_MIN:
        return False
    action["items"] = [items[0] + i * gap for i in range(len(items))]
    return True


def last_moment(action: dict) -> int | None:
    """The frame of an action's last step or counted item."""
    marks = list((action.get("step_at") or {}).values()) + list(action.get("items") or [])
    return max(marks) if marks else None


def realises(action: dict) -> set:
    """The relations a compiled or planned action shows (for the meaning check): refuse → reject, accept → accept,
    coin_count → limit and count, count_stack → count, the money templates → sequence and cause_effect."""
    name = action.get("template")
    return {"refuse": {"reject"}, "accept": {"accept"}, "coin_count": {"limit", "count"}, "count_stack": {"count"},
            "pay_change": {"sequence", "cause_effect", "change"}, "upi": {"sequence", "cause_effect"},
            "card_tap": {"sequence", "cause_effect"}, "cheque": {"sequence", "cause_effect", "change", "more_less"},
            "barter_swap": {"sequence", "compare"}, "hand_over": {"sequence"}}.get(name, set())


def action_beats(action: dict) -> set:
    """The beat ids an action's steps are cued in."""
    return {(s.get("cue") or [None])[0] for s in action.get("steps") or []} - {None}
