"""World plan → scene spec for the L3 ``world_scene`` block (Task 046 Part C, from the economy kit of 27 October 2026).

Same contract as the canvas plans (``bie/brain/canvas.py``): the director names props, people, effects and camera moves,
each on a cue word ([beat_id, word] or [beat_id, "", fraction]); this code turns cues into frames through
``timing.py`` and checks the plan (unknown kinds, cue words not in their beat, camera keys out of order, a crowd step
that is not a number, the picture staying still too long). This is Navin's "C" level: a part that tells a story with
actors in a place is shown inside a small designed world; the kits a world can draw are listed in ``KITS`` (a part whose
place has no kit falls back to the canvas, and the place goes to the missing-capability log). Kits so far: the shop street
(PR 1) and the bank (PR 3, for the Money chapter's v1: a worker saves ₹500 in an account, a borrower pays an EMI): a bank
building with a teller behind its counter, customers who walk in and out (the ``crowd``), and a ``board`` whose value
changes on cue (a passbook balance, an EMI due) with the old value struck out.

Task 046 Part D2 (Navin's verdict of 1 November 2026: "baat ho rahi hai kapda khareedne ki namak khareedne ki aur wo wahi
cheeni ko show kar rha hai"; "process show nahi ho rahi hai"): nothing in a world is hard-coded any more. The shop's goods, the
crowd's bags and the balance's pans are the story's own things (``goods``, ``carry.icon``, ``left``/``right``: icon ids the
icon index or the asset library resolved from the beat's nouns), and an ``action`` element is a kriya ka saancha
(``saanche.py``): the people of the story pay, scan, tap, swap, refuse and count on their cue words, the camera moves in to the
hands and the screen and back out. ``layout_problems`` is the stricter layout check: no overlap between boards, labels and the
action's people, at most one board, label or title on screen at a time, no number on a label (numbers go on objects), nothing
in the subtitle strip, an action's people at least about a quarter of the frame tall, and no camera key that shows an empty
street.
"""
from __future__ import annotations

import copy
import re

from .. import canvas
from .. import formats
from ..canvas import PlanError
from . import saanche, timing

KINDS = {"shop", "price_tag", "crowd", "coin_rain", "balance", "label", "pull_arrow", "title", "lamp", "foreground", "shopkeeper",
         "bank", "teller", "board", "action"}
GROUND = 860                     # the street's walking line in world pixels (world.tsx); a world is 1080 tall
FRAME_W, FRAME_H = 1920, 1080
SUBTITLE_TOP = 1 - canvas.SAFE["bottom"]            # the subtitle strip: the bottom 14 % of the frame is kept for the captions
CLOSE_ZOOM, CLOSE_Y = 1.6, 630                      # an action's close-up: the hands, the note, the phone screen, the passbook
MIN_ACTOR_SHARE = 0.25                              # Navin's D2 brief: an actor in a story piece at least about 1/4 of the frame height
ACTOR_PX = 300                                      # an action's people are 300 world pixels tall (saanche.tsx, s = 1)
TEXT_KINDS = ("board", "label", "title")            # at most one of these on screen at a time in a world (D2-D)
OVERLAY_KINDS = ("board", "label", "price_tag", "balance", "action")
# The places a story part can be set in (Navin, 27 October 2026: "a shop and its buyers, a bank and its borrowers, a factory
# and its workers, a port, a farm"), with the words that name them in a Hinglish script. A place with a kit in ``KITS`` goes
# to world mode (C); a place without one falls back to the canvas (B) and goes to the missing-capability log (Part C, PR 3
# builds the kits the chosen video needs). The director (bie/brain/canvas_director.py) decides; this module only draws.
PLACES = {
    # A tea stall, a market stall and the English "bazaar" are shops too (the Money chapter's v1, 28 October 2026).
    "shop": ("दुकान", "दुकानदार", "shop", "shopkeeper", "बाज़ार", "बाजार", "bazaar", "bazar", "market", "खरीदार", "buyer", "buyers", "ग्राहक",
             "customer", "customers", "किराना", "mandi", "मंडी", "tea stall", "stall", "stalls", "ठेला", "ठेले", "चायवाला", "चायवाले", "चाय"),
    # The bank's own words: accounts, deposits, savings, passbooks, instalments, the teller (never the English "account" alone:
    # money's "unit of account" is a shop story in v1).
    "bank": ("बैंक", "bank", "banks", "कर्ज़", "कर्ज", "loan", "loans", "borrower", "borrowers", "depositor", "depositors", "जमा", "उधार", "rbi",
             "खाता", "खाते", "passbook", "पासबुक", "savings", "बचत", "instalment", "installment", "किश्त", "क़िस्त", "teller", "cashier"),
    "factory": ("फैक्ट्री", "फ़ैक्ट्री", "factory", "factories", "कारखाना", "कारखाने", "मज़दूर", "मजदूर", "worker", "workers", "मशीन", "machine"),
    "port": ("बंदरगाह", "port", "ports", "ship", "ships", "जहाज़", "जहाज", "export", "exports", "import", "imports", "निर्यात", "आयात", "container"),
    "farm": ("खेत", "किसान", "farm", "farmer", "farmers", "फसल", "crop", "crops", "harvest", "कटाई", "tractor", "बीज"),
    # Navin's places for the real-world application (27 October 2026) add the petrol pump; a mandi and a kirana shop are shops.
    "petrol_pump": ("petrol pump", "पेट्रोल पंप", "पेट्रोल पम्प", "fuel station", "petrol", "diesel", "पेट्रोल", "डीज़ल", "डीजल"),
}
PLACE_LABELS = {"shop": "shop", "bank": "bank", "factory": "factory", "port": "port", "farm": "farm", "petrol_pump": "petrol pump"}
KITS = {"shop": {"label": "a shop with buyers on a street", "words": PLACES["shop"]},
        "bank": {"label": "a bank with its customers at the counter", "words": PLACES["bank"]}}
# The element kind that is a kit's place: a world plan for that kit must contain one (the other kinds dress the street).
PLACE_KINDS = {"shop": "shop", "bank": "bank"}
CUE_KEYS = ("cue", "until_cue", "tilt_cue")
# What a board, a price tag and the title can hold (the Money chapter's v1, 28 October 2026: the director wrote sentences into
# boards, 63 of 98 values over 16 characters, and they ran out of the box). A board holds up to BOARD_LINES lines of
# BOARD_CHARS characters (its own line breaks first, then long lines wrapped at spaces by code); a price tag shows a price;
# the title stays short. Longer text is refused with the limit named, so the maker says it in the narration or a label.
BOARD_LINES, BOARD_CHARS, TAG_CHARS, TITLE_CHARS = 2, 28, 9, 30      # 28 since 31 October 2026 (Task 046 Part D1): a board holds a name or a short
# phrase, never a sentence (Navin, 30 October: "sirf text hi text screen par dikha to video ... ek book ban jaayegi"); 40 on 29 October had let
# whole sentences sit on boards.


def wrap_value(text: str, width: int = BOARD_CHARS) -> list:
    """A board's value as lines: the maker's own line breaks are kept, a longer line is wrapped at its spaces."""
    out = []
    for line in str(text or "").split("\n"):
        cur = ""
        for word in line.split(" "):
            if not cur:
                cur = word
            elif len(cur) + 1 + len(word) <= width:
                cur += " " + word
            else:
                out.append(cur)
                cur = word
        out.append(cur)
    return out


def _check_text(n: dict) -> None:
    """The text limits of a board, a price tag and the title (PlanError names the limit and what to do instead)."""
    kind, nid = n.get("kind"), n.get("id", "?")
    if kind == "board":
        for st in n.get("steps") or []:
            lines = wrap_value(st.get("text", ""))
            if len(lines) > BOARD_LINES or any(len(line) > BOARD_CHARS for line in lines):
                raise PlanError(f"{nid}: a board holds at most {BOARD_LINES} lines of {BOARD_CHARS} characters, and "
                                f"'{str(st.get('text', ''))[:40]}' needs {len(lines)} lines: say the rest in the narration, or split it "
                                "over two steps on two cue words")
            st["lines"] = lines
    elif kind == "price_tag":
        for st in n.get("steps") or []:
            if len(str(st.get("text", ""))) > TAG_CHARS:
                raise PlanError(f"{nid}: a price tag shows a price ('₹65', '₹10,000'; at most {TAG_CHARS} characters), not "
                                f"'{str(st.get('text', ''))[:30]}': use a board for words")
    elif kind == "title" and len(str(n.get("text", ""))) > TITLE_CHARS:
        raise PlanError(f"{nid}: the title is at most {TITLE_CHARS} characters ('{str(n.get('text', ''))[:40]}' has "
                        f"{len(str(n.get('text', '')))})")


def _src(icon_paths, icon) -> str:
    return (icon_paths or {}).get(icon, icon)


def icons_in(plan: dict) -> list:
    """Every icon id a world plan names (the shop's goods, the crowd's bags, the balance's pans, the actions' objects), once
    each, in order."""
    out = []
    for e in plan.get("elements") or []:
        refs = [g.get("icon") for g in e.get("goods") or []] + [(e.get("carry") or {}).get("icon")]
        refs += [(e.get(side) or {}).get("icon") for side in ("left", "right")]
        if e.get("kind") == "action":
            refs += saanche.icons_of(e)
        for ref in refs:
            if ref and ref not in out:
                out.append(ref)
    return out


def goods_problems(plan: dict) -> list:
    """Story goods from the story (D2-A): a shop that shows its stock names the goods, a crowd that carries bags names what is in
    them, a balance names what is on each pan; nothing is drawn from a fixed picture (the D1 videos showed sugar for salt and
    cloth)."""
    out = []
    for e in plan.get("elements") or []:
        kind, eid = e.get("kind"), e.get("id", "?")
        if kind == "shop" and e.get("packets") and not any(g.get("icon") for g in e.get("goods") or []):
            out.append(f"{eid}: the shop's stock is the story's goods: name them in goods ([{{icon, label}}], an icon from the "
                       "candidates for the thing the beat names); nothing is drawn by default")
        if kind == "crowd" and e.get("carry") and not (e.get("carry") or {}).get("icon"):
            out.append(f"{eid}: the buyers carry the story's goods: give carry_icon (the thing the beat names)")
        if kind == "balance" and not all((e.get(side) or {}).get("icon") for side in ("left", "right")):
            out.append(f"{eid}: a balance weighs the story's things: give left_icon and right_icon (with left_label, right_label)")
    return out


def main_look_of(plan: dict) -> int:
    """The main character's look for the video the plan belongs to (the plan id is ``<video>_<part>``)."""
    vid = plan.get("video_id") or str(plan.get("id", "world")).split("_")[0]
    return saanche.main_look(vid)


def _close_ups(cam: list, actions: list) -> list:
    """The camera moves in to each action's close-up step and back out to where the plan's camera was going: the plan's keys
    inside a close-up are replaced by it, the key after it brings the plan's view back."""
    keys = [dict(k) for k in cam]
    for a in sorted(actions, key=lambda a: (a.get("close_up") or {}).get("at", 0)):
        cu = a.get("close_up")
        if not cu:
            continue
        before = [k for k in keys if k["at"] <= cu["until"] and not k.get("close_up")]
        back = dict(before[-1]) if before else dict(keys[0])
        keys = [k for k in keys if not (cu["at"] <= k["at"] <= cu["until"])]
        keys.append({"at": cu["at"], "x": a["x"], "y": CLOSE_Y, "zoom": CLOSE_ZOOM, "frames": 22, "close_up": a["id"]})
        keys.append({"at": cu["until"], "x": back["x"], "y": back.get("y", 540), "zoom": back.get("zoom", 1.0), "frames": 30, "back": a["id"]})
        keys.sort(key=lambda k: k["at"])
    # a close-up that starts within a second of the last one's way back stays close (no in-out-in jolt)
    out = []
    for k in keys:
        if k.get("close_up") and out and out[-1].get("back") and k["at"] - out[-1]["at"] < 36:
            out.pop()
        out.append(k)
    return [{n: v for n, v in k.items() if n != "back"} for k in out]


def compile_world(plan: dict, *, voice: dict | None = None, lead_in: float = timing.LEAD_IN, kit: str = "",
                  icon_paths: dict | None = None, main_look: int | None = None):
    """(scene, report) for a world plan; ``kit`` (or ``plan["kit"]``) names the kit the plan was written for, so a bank story
    is refused until it has its bank (a shop drawn for a bank story is the wrong world). ``icon_paths`` maps the plan's icon
    ids to the files the render copies; ``main_look`` is the video's main character (``main_look_of``)."""
    kit = kit or plan.get("kit") or ""
    main_look = main_look_of(plan) if main_look is None else main_look
    beats = plan["beats"]
    if not beats:
        raise PlanError("a world plan needs at least one beat")
    says = {b["beat_id"]: b["say"] for b in beats}
    sid = plan.get("id", "world")
    voice = voice if voice is not None else formats.voice_of(beats)      # Task 047: the spoken words, once the voice section writes them
    tl = timing.build(beats, [{"scene_id": sid, "beat_ids": [b["beat_id"] for b in beats]}], voice=voice, lead_in=lead_in)
    fps = tl[sid]["fps"]

    def frame_of(cue):
        return canvas.cue_frame(tl, sid, says, cue)

    changes = []
    els = []
    spans = {bid: tuple(v) for bid, v in tl[sid]["beats"].items()}
    for n in copy.deepcopy(plan.get("elements") or []):
        if n.get("kind") not in KINDS:
            raise PlanError(f"{n.get('id', '?')}: unknown world element kind {n.get('kind')!r} (kinds: {', '.join(sorted(KINDS))})")
        if n["kind"] == "action":                     # a kriya ka saancha (D2-B): code times its steps, the block draws them
            a = saanche.compile_action(n, frame_of, says, icon_paths=icon_paths, main_look=main_look, beat_spans=spans)
            a["x"] = n.get("x", 2600)
            # beside the shop or the bank the action uses the place's own counter (the stage draws one only on an empty street)
            a["on_place"] = any(e.get("kind") in PLACE_KINDS.values() and abs(e.get("x", 0) - a["x"]) < 520
                                for e in plan.get("elements") or [])
            changes += list(a["step_at"].values()) + a.get("items", []) + ([a["until"]] if "until" in a else [])
            els.append(a)
            continue
        _check_text(n)
        for g in n.get("goods") or []:
            g["src"] = _src(icon_paths, g.get("icon", ""))
        for key in ("carry", "left", "right"):
            if (n.get(key) or {}).get("icon"):
                n[key]["src"] = _src(icon_paths, n[key]["icon"])
        if "cue" in n:
            n["at"] = frame_of(n.pop("cue")); changes.append(n["at"])
        if "until_cue" in n:
            n["until"] = frame_of(n.pop("until_cue")); changes.append(n["until"])
        if "tilt_cue" in n:
            n["tilt_at"] = frame_of(n.pop("tilt_cue")); changes.append(n["tilt_at"])
        for key in ("steps", "packets"):
            for st in n.get(key, []):
                st["at"] = frame_of(st.pop("cue")); changes.append(st["at"])
                if "n" in st and (isinstance(st["n"], bool) or not isinstance(st["n"], int) or st["n"] < 0):
                    raise PlanError(f"{n['id']}: a step count must be a whole number")
        for key in ("lift", "carry"):
            if key in n:
                n[key]["at"] = frame_of(n[key].pop("cue")); changes.append(n[key]["at"])
        els.append(n)
    kinds = {e["kind"] for e in els}
    places = [k for k, kind in PLACE_KINDS.items() if kind in kinds]
    if kit and PLACE_KINDS.get(kit) not in kinds:
        raise PlanError(f"a world in {place_label(kit)} needs its place: add a {PLACE_KINDS.get(kit, kit)} element")
    if not places:
        raise PlanError("a world needs its place: add a " + " or a ".join(PLACE_KINDS.values()) + " element (the kits so far)")
    cam = []
    for k in plan.get("camera") or []:
        f = frame_of(k["cue"])
        if cam and f < cam[-1]["at"]:
            raise PlanError("camera keys must be in time order")
        cam.append({"at": f, "x": k["x"], "y": k.get("y", 540), "zoom": k.get("zoom", 1.0), "frames": k.get("frames", 36)})
        changes.append(f)
    if not cam:
        raise PlanError("a world needs at least one camera key")
    cam = _close_ups(cam, [e for e in els if e["kind"] == "action"])
    changes += [k["at"] for k in cam]
    duration = tl[sid]["duration"]
    pts = sorted(set(changes)) + [duration]
    still = max(b - a for a, b in zip(pts, pts[1:])) / fps
    problems = [f"the picture stays the same for {still:.1f} s (limit {canvas.MAX_STILL_S:.0f} s)"] if still > canvas.MAX_STILL_S else []
    data = {"world_width": plan.get("world_width", 5200), "elements": els, "camera": cam}
    scene = {"id": sid, "duration": duration, "camera": [{"at": 0}], "captions": canvas.captions_of(tl, sid, beats),
             "layers": [{"id": sid + "_world", "type": "block", "block": "world_scene", "at": 0, "box": {"x": 0, "y": 0, "w": 1, "h": 1}, "data": data}]}
    report = {"scene": sid, "seconds": round(duration / fps, 1), "elements": len(els), "camera_moves": len(cam),
              "longest_still_s": round(still, 1), "change_every_s": round(duration / fps / max(1, len(pts) - 1), 1), "problems": problems,
              "mode": "C", "level": "L3", "kit": kit or places[0], "actions": [e["template"] for e in els if e["kind"] == "action"]}
    return scene, report


# ---------------------------------------------------------------- the stricter layout check (Task 046 Part D2, D)

def _ease(t: float) -> float:
    t = min(1.0, max(0.0, t))
    return 4 * t * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2         # Easing.inOut(Easing.cubic), as world.tsx


def cam_at(keys: list, frame: int) -> dict:
    """The camera at a frame, exactly as world.tsx ``camAt`` moves it."""
    c = {"x": keys[0]["x"], "y": keys[0].get("y", 540), "zoom": keys[0].get("zoom", 1.0)}
    for k in keys:
        if frame < k["at"]:
            break
        t = _ease((frame - k["at"]) / max(1, k.get("frames", 36)))
        c = {name: c[name] + (k.get(name, 540 if name == "y" else 1.0) - c[name]) * t for name in ("x", "y", "zoom")}
    return c


def board_size(el: dict) -> tuple:
    """A board's width and height in world pixels, as world.tsx ``Board`` sizes it for its longest step."""
    w = h = 0
    for st in el.get("steps") or []:
        lines = st.get("lines") or wrap_value(st.get("text", ""))
        longest = max([1] + [len(line) for line in lines])
        fs = 96 if len(lines) == 1 and longest <= 8 else 72 if len(lines) == 1 and longest <= 14 else 46 if longest <= 26 else 36
        w = max(w, max(440, min(1100 if longest > 26 else 960, round(longest * fs * 0.6 + 90))))
        h = max(h, max(310, round(140 + len(lines) * fs * 1.22 + 40)))
    return w, h


def box_of(el: dict) -> tuple | None:
    """An overlay's box in world pixels (x0, y0, x1, y1), or None for a kind that is the place itself."""
    kind = el.get("kind")
    x, y = el.get("x", 0), el.get("y", 540)
    if kind == "board":
        w, h = board_size(el)
        return (x - w / 2, y - h / 2, x + w / 2, y + h / 2)
    if kind == "label":
        size = el.get("size", 34)
        w = len(str(el.get("text", ""))) * size * 0.62 + 56
        return (x - w / 2, y - 34, x + w / 2, y + 34)
    if kind == "price_tag":
        dy = (el.get("lift") or {}).get("dy", 0)
        return (x - 110, y - 40 - dy, x + 130, y + 80)
    if kind == "balance":
        sc = el.get("scale", 1.25)
        return (x - 300 * sc, y - 60 * sc, x + 300 * sc, y + 300 * sc)
    if kind == "action":
        top = GROUND - saanche.FEET + ACTION_TOP.get(el.get("template"), 120)
        return (x - saanche.STAGE_W / 2 + 60, top, x + saanche.STAGE_W / 2 - 60, GROUND)
    return None


# where an action's drawing starts above its stage (stage units from the stage top): its bubbles, phone cards and meter
ACTION_TOP = {"upi": 20, "barter_swap": 90, "coin_count": 120, "cheque": 200, "pay_change": 240, "card_tap": 230, "hand_over": 240,
              "refuse": 150, "accept": 150, "count_stack": 120}         # the name tags stand above the heads, at 248


def _on(el: dict, duration: int) -> tuple:
    start = el.get("at")
    if start is None:
        starts = [st["at"] for st in el.get("steps") or [] if "at" in st] + list((el.get("step_at") or {}).values())
        start = min(starts) if starts else 0
    return start, el.get("until", duration)


def _screen(box: tuple, cam: dict) -> tuple:
    z = cam["zoom"]
    return (FRAME_W / 2 + z * (box[0] - cam["x"]), FRAME_H / 2 + z * (box[1] - cam["y"]),
            FRAME_W / 2 + z * (box[2] - cam["x"]), FRAME_H / 2 + z * (box[3] - cam["y"]))


NUMBER_ON_LABEL = re.compile(r"\d")


def layout_problems(scene: dict, *, step: int = 6) -> list:
    """The stricter world layout (Navin's D2 brief, D): no overlap between boards, labels, price tags, balances and the action's
    people while they are on screen together; at most one board, label or title at a time; no number on a label or the title
    (numbers go on objects: the price tag, the note, the phone screen, the passbook board); nothing in the subtitle strip; an
    action's people at least about a quarter of the frame tall and inside the frame; no camera key that shows an empty street."""
    layer = scene["layers"][0]["data"]
    els, cam, duration = layer["elements"], layer["camera"], scene["duration"]
    out = []
    shown = [(e, box_of(e), _on(e, duration)) for e in els if e.get("kind") in OVERLAY_KINDS]
    shown = [s for s in shown if s[1]]
    for i, (a, ba, (a0, a1)) in enumerate(shown):
        for b, bb, (b0, b1) in shown[i + 1:]:
            if max(a0, b0) < min(a1, b1) and ba[0] < bb[2] and bb[0] < ba[2] and ba[1] < bb[3] and bb[1] < ba[3]:
                out.append(f"{a['id']} and {b['id']} overlap while both are on screen: move one (x, y) or let the first leave (until_cue)")
    for e in els:
        if e.get("kind") in ("label", "title") and NUMBER_ON_LABEL.search(str(e.get("text", ""))):
            out.append(f"{e['id']}: a {e['kind']} has no number ('{e.get('text', '')}'); in a world numbers go on objects: a price tag, "
                       "the note or the phone screen of an action, a passbook board")
    texts = [(e, _on(e, duration)) for e in els if e.get("kind") in TEXT_KINDS]
    for f in range(0, duration, step):
        live = [e["id"] for e, (t0, t1) in texts if t0 <= f < t1]
        if len(live) > 1:
            out.append(f"{', '.join(live)} are on screen together at {f / timing.FPS:.1f} s: in a world at most one board, label or "
                       "title is on screen at a time (give the first an until_cue)")
            break
    strip = SUBTITLE_TOP * FRAME_H
    flagged = set()                                   # (element id, problem): each problem named once per element
    for f in range(0, duration, step):
        c = cam_at(cam, f)
        for e, box, (t0, t1) in shown:
            if not t0 + 12 <= f < t1:
                continue
            sb = _screen(box if e["kind"] != "action" else (box[0], box[1], box[2], GROUND - 10), c)
            visible = sb[2] > 0 and sb[0] < FRAME_W and sb[3] > 0 and sb[1] < FRAME_H
            if visible and sb[3] > strip + 1 and (e["id"], "strip") not in flagged:
                flagged.add((e["id"], "strip"))
                out.append(f"{e['id']} reaches into the subtitle strip at {f / timing.FPS:.1f} s (its bottom at {sb[3] / FRAME_H:.2f} of the "
                           f"frame, the strip starts at {SUBTITLE_TOP:.2f}): raise it (y) or move the camera (y, zoom)")
            if e["kind"] != "action" or not visible:
                continue
            tall = ACTOR_PX * c["zoom"] / FRAME_H
            if tall < MIN_ACTOR_SHARE - 0.02 and (e["id"], "small") not in flagged:
                flagged.add((e["id"], "small"))
                out.append(f"{e['id']}: its people are {tall:.2f} of the frame tall at {f / timing.FPS:.1f} s (at least {MIN_ACTOR_SHARE}): "
                           "zoom the camera to 0.9 or more while the action plays")
            if not (sb[0] >= -40 and sb[2] <= FRAME_W + 40) and (e["id"], "cut") not in flagged and _settled(cam, f):
                flagged.add((e["id"], "cut"))
                out.append(f"{e['id']} is cut by the frame at {f / timing.FPS:.1f} s: centre a camera key on its x ({e['x']})")
    spots = [(b[0], b[2]) for e in els for b in [box_of(e) or _place_span(e)] if b]
    for k in cam:
        half = FRAME_W / 2 / max(0.3, k.get("zoom", 1.0))
        if spots and not any(x0 < k["x"] + half and x1 > k["x"] - half for x0, x1 in spots):
            out.append(f"the camera key at {k['at'] / timing.FPS:.1f} s (x {k['x']}) shows an empty street: point it at the place, "
                       "the people or the action")
    return out


def _settled(cam: list, frame: int) -> bool:
    """The camera is not between two keys at this frame (a frame cut while the camera glides past is not a still)."""
    return not any(k["at"] <= frame < k["at"] + k.get("frames", 36) for k in cam)


def _place_span(e: dict):
    half = {"shop": 420, "bank": 500, "teller": 60, "shopkeeper": 60}.get(e.get("kind"))
    if half:
        return (e.get("x", 0) - half, 0, e.get("x", 0) + half, GROUND)
    if e.get("kind") == "crowd":
        return (e.get("x0", 0) - 60, 0, e.get("x0", 0) + 6 * e.get("spacing", 120), GROUND)
    return None


def place_of(text: str) -> str:
    """The place a part's words name (the place named most often wins), or "" for a part that is not a story in a place."""
    low = text.lower()
    counts = {place: sum(low.count(w.lower()) for w in words) for place, words in PLACES.items()}
    best = max(counts, key=counts.get)
    return best if counts[best] else ""


def kit_for(text: str) -> str:
    """The world kit for a part's place, or "" when the place has no kit yet (or the part has no place)."""
    place = place_of(text)
    return place if place in KITS else ""


def place_label(place: str) -> str:
    """The words of a place for a report or the missing-capability log ("petrol_pump" → "petrol pump")."""
    return PLACE_LABELS.get(place, place.replace("_", " "))
