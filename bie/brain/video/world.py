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
import json
import re
from pathlib import Path

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
_PLACES_DATA = json.loads((Path(__file__).resolve().parents[1] / "rulebook" / "places.json").read_text(encoding="utf-8"))
PLACES = {k: tuple(v) for k, v in _PLACES_DATA["places"].items()}
# What each element kind draws, by the words that name the thing, and the kinds that stand in the street for the whole part
# (the kit's place and the person who works there); the coverage check (bie/brain/visual_thinking.coverage_rows) reads both.
DRAWS = {k: frozenset(w.lower() for w in v) for k, v in _PLACES_DATA.get("draws", {}).items() if not k.startswith("_")}
WHOLE_PART_KINDS = frozenset(_PLACES_DATA.get("whole_part", {}).get("kinds", ()))
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
                raise PlanError(f"{nid}: a price tag shows a price (a number with its sign; at most {TAG_CHARS} characters), not "
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


def _close_ups(cam: list, actions: list, fixes: list | None = None) -> list:
    """The camera moves in to each action's close-up step and back out to where the plan's camera was going: the plan's keys
    inside a close-up are replaced by it, the key after it brings the plan's view back. A close-up ends when its action leaves
    or when code framed another action that starts meanwhile (seekh -> BIE, the first Part D2 run: a close-up held on a stage
    whose people had gone while the next process played off screen)."""
    keys = [dict(k) for k in cam]
    fixes = fixes if fixes is not None else []
    for a in sorted(actions, key=lambda a: (a.get("close_up") or {}).get("at", 0)):
        cu = a.get("close_up")
        if not cu:
            continue
        end = min(cu["until"], a.get("until", 10 ** 9))
        other = next((k for k in sorted(keys, key=lambda k: k["at"])
                      if k.get("frame") and k["frame"] != a["id"] and cu["at"] < k["at"] < end), None)
        if other:
            end = other["at"]
        if end < cu["until"]:
            fixes.append(f"the close-up on {a['id']} ends at {end}, when " +
                         (f"{other['frame']} starts" if other else f"{a['id']} leaves"))
            cu["until"] = end
        if end - cu["at"] < 24:                  # too short to move in and out: the camera stays where it is
            a.pop("close_up")
            continue
        before = [k for k in keys if k["at"] <= end and not k.get("close_up")]
        back = dict(before[-1]) if before else dict(keys[0])
        keys = [k for k in keys if not (cu["at"] <= k["at"] <= end) or k is other]
        keys.append({"at": cu["at"], "x": a["x"], "y": CLOSE_Y, "zoom": CLOSE_ZOOM, "frames": 22, "close_up": a["id"]})
        if not other:
            keys.append({"at": end, "x": back["x"], "y": back.get("y", 540), "zoom": back.get("zoom", 1.0), "frames": 30, "back": a["id"]})
        keys.sort(key=lambda k: k["at"])
    # a close-up that starts within a second of the last one's way back stays close (no in-out-in jolt)
    out = []
    for k in keys:
        if k.get("close_up") and out and out[-1].get("back") and k["at"] - out[-1]["at"] < 36:
            out.pop()
        out.append(k)
    return [{n: v for n, v in k.items() if n not in ("back", "frame")} for k in out]


def _frame_actions(cam: list, els: list, fixes: list) -> tuple:
    """Each action is in the frame when it starts (seekh -> BIE: 6 of 88 refused rounds in the first Part D2 run were an action
    the plan's camera cut): where the camera at the action's start does not hold its stage, code adds a key on the action's x
    at its start, zoomed to at least 0.9 so its people are a quarter of the frame tall."""
    keys = [dict(k) for k in cam]
    for a in sorted((e for e in els if e["kind"] == "action"), key=lambda e: e["at"]):
        box = box_of(a)
        c = cam_at(keys, a["at"] + 24)
        half = FRAME_W / 2 / max(0.3, c["zoom"])
        inside = box[0] >= c["x"] - half - 40 and box[2] <= c["x"] + half + 40
        if inside and c["zoom"] >= 0.9:
            continue
        keys.append({"at": a["at"], "x": a["x"], "y": c["y"], "zoom": max(c["zoom"], 1.0), "frames": 24, "frame": a["id"]})
        keys.sort(key=lambda k: k["at"])
        fixes.append(f"camera key added on {a['id']} at its start (x {a['x']})")
    acts = [e for e in els if e["kind"] == "action"]
    for i, k in enumerate(keys):                 # a key whose view cuts the actions on screen while it holds is widened
        t0 = k["at"] + k.get("frames", 36)
        t1 = keys[i + 1]["at"] if i + 1 < len(keys) else 10 ** 9
        live = [a for a in acts if a["at"] < t1 and a.get("until", 10 ** 9) > t0]
        if not live:
            continue
        x0, x1 = min(box_of(a)[0] for a in live), max(box_of(a)[2] for a in live)
        half = FRAME_W / 2 / max(0.3, k.get("zoom", 1.0))
        if x0 >= k["x"] - half - 40 and x1 <= k["x"] + half + 40:
            continue
        zoom = min(k.get("zoom", 1.0), FRAME_W / (x1 - x0 + 80))
        if any(a.get("actors") for a in live) and zoom < 0.9:
            continue                             # people would be too small: the maker places them apart in time
        k.update(x=round((x0 + x1) / 2), zoom=round(zoom, 3))
        fixes.append(f"camera key at {k['at']} widened to hold {', '.join(a['id'] for a in live)}")
    return keys, fixes


def settle_places(els: list, duration: int, *, place: bool = True) -> list:
    """The places and times code settles before the camera is framed (seekh -> BIE: overlaps were 37 of the first Part D2 run's
    refusals): an until before its own cue is dropped (the element would never show); two actions starting together on one spot
    stand side by side; two overlays (board, label, price tag, balance, action) in the same place, one starting at least 12
    frames after the other, follow each other (the first leaves when the second comes, as the check's own advice says); the
    same for two of board, label and title on screen together (one text at a time). In place; returns what was done. With
    ``place=False`` (the pass after the camera is framed) nothing moves: only who leaves when."""
    fixes = []
    for e in els:                                # an until before the element's own start: it would never show
        if "until" in e and e["until"] <= _on(e, duration)[0]:
            e.pop("until")
            fixes.append(f"{e['id']}: its until came before its cue and was dropped")
    starts = {id(e): _on(e, duration)[0] for e in els}
    acts = [e for e in els if e.get("kind") == "action"] if place else []
    for i, a in enumerate(acts):                 # two actions starting together on one spot: the second steps aside
        for b in acts[i + 1:]:
            ba, bb = box_of(a), box_of(b)
            if abs(starts[id(a)] - starts[id(b)]) < 12 and ba[0] < bb[2] and bb[0] < ba[2] and \
                    max(starts[id(a)], starts[id(b)]) < min(a.get("until", 10 ** 9), b.get("until", 10 ** 9)):
                b["x"] = a["x"] + saanche.STAGE_W
                fixes.append(f"{b['id']} moved beside {a['id']} (x {b['x']}): they start together")
    def leave(first, second, why):
        saanche.fit_items(first, starts[id(second)])
        last_step = saanche.last_moment(first)
        if last_step is not None and starts[id(second)] < last_step + 30:
            nxt = min((second.get("step_at") or {}).values(), default=starts[id(second)])
            done = canvas.hand_over_after(first, second, last_step, nxt)
            if done:                             # the next thing comes on after the first's last step (an action by its first step)
                starts[id(second)] = second["at"]
                fixes.append(done)
                return True
            return False                         # an action never leaves before it has played: a real clash for the maker
        first["until"] = starts[id(second)]
        fixes.append(f"{first['id']} leaves when {second['id']} comes ({why})")
        return True
    for _ in range(3):
        changed = False
        shown = sorted((e for e in els if e.get("kind") in OVERLAY_KINDS and box_of(e)), key=lambda e: starts[id(e)])
        for i, a in enumerate(shown):
            for b in shown[i + 1:]:
                a0, a1 = _on(a, duration)
                b0, b1 = _on(b, duration)
                ba, bb = box_of(a), box_of(b)
                together = max(a0, b0) < min(a1, b1)
                touching = ba[0] < bb[2] and bb[0] < ba[2] and ba[1] < bb[3] and bb[1] < ba[3]
                if not (together and touching):
                    continue
                if b0 - a0 >= 12 and leave(a, b, "same place"):
                    changed = True
                elif not place:
                    continue
                elif a.get("kind") == "action" and b.get("kind") == "action":
                    b["x"] = a["x"] + saanche.STAGE_W            # the second process plays beside the first, not on it
                    fixes.append(f"{b['id']} moved beside {a['id']} (x {b['x']}): it starts while {a['id']} plays")
                    changed = True
                elif "action" in (a.get("kind"), b.get("kind")):
                    act, over = (a, b) if a.get("kind") == "action" else (b, a)
                    bo, ba_ = box_of(over), box_of(act)
                    h = bo[3] - bo[1]
                    if over.get("kind") in ("board", "label", "price_tag") and ba_[1] - h - 20 >= 40:
                        over["y"] = round(ba_[1] - 20 - (bo[3] - over.get("y", 540)))   # above the action's drawing
                        fixes.append(f"{over['id']} raised above {act['id']}")
                        changed = True
        texts = sorted((e for e in els if e.get("kind") in TEXT_KINDS), key=lambda e: starts[id(e)])
        for i, a in enumerate(texts):
            for b in texts[i + 1:]:
                a0, a1 = _on(a, duration)
                b0, b1 = _on(b, duration)
                if max(a0, b0) < min(a1, b1) and b0 - a0 >= 12 and leave(a, b, "one text at a time"):
                    changed = True
        if not changed:
            break
    if place:
        fixes += _fill_gaps(els, duration)
    return fixes


GAP_FILL = 60                    # frames: a stage left empty for up to 2 s between two actions on one spot keeps the first


def _fill_gaps(els: list, duration: int) -> list:
    """Two actions on one spot with a short gap between them hand over without an empty stage (seekh -> BIE, the first Part D2
    run: v2_s4s showed an empty street for 1.2 s between a refusal and the agreement that followed it): the first stays until
    the second comes, unless something else is shown on that spot meanwhile."""
    fixes = []
    acts = sorted((e for e in els if e.get("kind") == "action"), key=lambda e: _on(e, duration)[0])
    for i, a in enumerate(acts):
        if "until" not in a:
            continue
        ba = box_of(a)
        nxt = next((b for b in acts[i + 1:] if _on(b, duration)[0] >= a["until"] and box_of(b)[0] < ba[2] and ba[0] < box_of(b)[2]), None)
        if not nxt or _on(nxt, duration)[0] - a["until"] > GAP_FILL:
            continue
        t0, t1 = a["until"], _on(nxt, duration)[0]
        busy = [o for o in els if o is not a and o is not nxt and box_of(o) and box_of(o)[0] < ba[2] and ba[0] < box_of(o)[2]
                and max(t0, _on(o, duration)[0]) < min(t1, _on(o, duration)[1])]
        if busy or t1 == t0:
            continue
        a["until"] = t1
        if a.get("close_up") and a["close_up"]["until"] > t1:
            a["close_up"]["until"] = t1
        fixes.append(f"{a['id']} stays until {nxt['id']} comes (the stage was empty for {(t1 - t0) / timing.FPS:.1f} s)")
    return fixes


def settle_layout(els: list, cam: list, duration: int) -> list:
    """The view code settles after the camera is framed: the camera looks low enough that an action's feet stay above the
    subtitle strip, and a board, label, price tag or balance reaching into the strip is raised just above it."""
    fixes = []
    acts = [e for e in els if e.get("kind") == "action"]
    strip = SUBTITLE_TOP * FRAME_H
    for i, k in enumerate(cam):                  # the camera looks low enough that the action's feet stay above the strip
        if k.get("close_up"):
            continue
        t1 = cam[i + 1]["at"] if i + 1 < len(cam) else duration
        if any(a["at"] < t1 and a.get("until", 10 ** 9) > k["at"] for a in acts):
            need = (GROUND - 10) - (strip - FRAME_H / 2 - 2) / max(0.3, k.get("zoom", 1.0))
            if k.get("y", 540) < need:
                k["y"] = round(need + 0.5)
                fixes.append(f"camera key at {k['at']} looks {round(need - 540)} px lower so the feet stay above the subtitle strip")
    fixes += _split_dips(cam, acts, duration)
    for e in els:
        if e.get("kind") not in ("board", "label", "price_tag", "balance"):
            continue
        t0, t1 = _on(e, duration)
        worst = 0.0
        for f in range(t0 + 12, min(t1, duration), 6):
            c = cam_at(cam, f)
            sb = _screen(box_of(e), c)
            if sb[2] > 0 and sb[0] < FRAME_W and sb[3] > strip:
                worst = max(worst, (sb[3] - strip + 8) / c["zoom"])
        if worst:
            e["y"] = round(e.get("y", 540) - worst)
            fixes.append(f"{e['id']} raised {round(worst)} px above the subtitle strip")
    return fixes


def _split_dips(cam: list, acts: list, duration: int) -> list:
    """A camera move that zooms and pans together can push the feet into the subtitle strip half-way even when both ends keep
    them above it (seekh -> BIE, Part D2 run b: v2_s4s refused three rounds for a dip at 41.0 s while the camera moved from a wide
    view into a close-up). Where an action plays during such a move, code splits it in two: first the change that lifts the
    feet (the pan when zooming in, the zoom when zooming out), then the other, in the same time. In place."""
    fixes = []
    limit = SUBTITLE_TOP * FRAME_H - FRAME_H / 2 - 2      # zoom × (feet − camera y) must stay below this
    feet = GROUND - 10
    i = 1
    while i < len(cam):
        k = cam[i]
        frames = k.get("frames", 36)
        live = any(a["at"] < k["at"] + frames and a.get("until", 10 ** 9) > k["at"] for a in acts)
        if not live or frames < 12:
            i += 1
            continue
        c = cam_at(cam, k["at"])
        z0, h0 = c["zoom"], feet - c["y"]
        z1, h1 = k.get("zoom", 1.0), feet - k.get("y", 540)
        worst = max((z0 + (z1 - z0) * e / 20) * (h0 + (h1 - h0) * e / 20) for e in range(21))
        if worst <= limit + 0.5:
            i += 1
            continue
        if z0 * h1 <= limit:                     # pan first, then zoom
            mid = {"x": k["x"], "y": k.get("y", 540), "zoom": z0}
        elif z1 * h0 <= limit:                   # zoom first, then pan
            mid = {"x": k["x"], "y": c["y"], "zoom": z1}
        else:
            i += 1
            continue
        half = frames // 2
        cam.insert(i, dict(mid, at=k["at"], frames=half))
        k["at"] += half
        k["frames"] = frames - half
        fixes.append(f"camera move at {cam[i]['at']} split in two so the feet stay above the subtitle strip on the way")
        i += 2
    return fixes


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
    fixes = [f for e in els for f in e.pop("auto_fixes", [])]
    for k in plan.get("camera") or []:
        f = frame_of(k["cue"])
        cam.append({"at": f, "x": k["x"], "y": k.get("y", 540), "zoom": k.get("zoom", 1.0), "frames": k.get("frames", 36)})
        changes.append(f)
    if not cam:
        raise PlanError("a world needs at least one camera key")
    if [k["at"] for k in cam] != sorted(k["at"] for k in cam):          # seekh -> BIE: code puts the keys in time order
        cam.sort(key=lambda k: k["at"])
        fixes.append("camera keys put in time order")
    duration = tl[sid]["duration"]
    fixes += settle_places(els, duration)
    cam, fixes = _frame_actions(cam, els, fixes)
    cam = _close_ups(cam, [e for e in els if e["kind"] == "action"], fixes)
    changes += [k["at"] for k in cam]
    fixes += settle_layout(els, cam, duration)
    fixes += settle_places(els, duration, place=False)   # a raise above the strip can meet another overlay: the first leaves
    pts = sorted(set(changes)) + [duration]
    still = max(b - a for a, b in zip(pts, pts[1:])) / fps
    problems = [f"the picture stays the same for {still:.1f} s (limit {canvas.MAX_STILL_S:.0f} s)"] if still > canvas.MAX_STILL_S else []
    data = {"world_width": plan.get("world_width", 5200), "elements": els, "camera": cam}
    scene = {"id": sid, "duration": duration, "camera": [{"at": 0}], "captions": canvas.captions_of(tl, sid, beats),
             "layers": [{"id": sid + "_world", "type": "block", "block": "world_scene", "at": 0, "box": {"x": 0, "y": 0, "w": 1, "h": 1}, "data": data}]}
    report = {"scene": sid, "seconds": round(duration / fps, 1), "elements": len(els), "camera_moves": len(cam),
              "longest_still_s": round(still, 1), "change_every_s": round(duration / fps / max(1, len(pts) - 1), 1), "problems": problems,
              "mode": "C", "level": "L3", "kit": kit or places[0], "actions": [e["template"] for e in els if e["kind"] == "action"],
              "auto_fixes": fixes}
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
        top = GROUND - saanche.FEET + saanche.top_of(el)
        return (x - saanche.STAGE_W / 2 + 60, top, x + saanche.STAGE_W / 2 - 60, GROUND)
    return None



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
                act = next((e for e in (a, b) if e.get("kind") == "action" and e.get("step_at")), None)
                why = (f" ({act['id']} stays until {saanche.PLAYED} frames after its last step, at "
                       f"{(max(act['step_at'].values()) + saanche.PLAYED) / timing.FPS:.1f} s: cue the other after that or move it)") if act else ""
                out.append(f"{a['id']} and {b['id']} overlap while both are on screen: move one (x, y) or let the first leave (until_cue){why}")
    for e in els:
        if e.get("kind") in ("label", "title") and NUMBER_ON_LABEL.search(str(e.get("text", ""))):
            out.append(f"{e['id']}: a {e['kind']} has no number ('{e.get('text', '')}'); in a world numbers go on objects: a price tag, "
                       "a tag, sign, screen or meter of an action, a board")
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
            active = next((k for k in reversed(cam) if k["at"] <= f), None)
            closing_on_other = bool(active and active.get("close_up") and active["close_up"] != e["id"])
            if not (sb[0] >= -40 and sb[2] <= FRAME_W + 40) and (e["id"], "cut") not in flagged and _settled(cam, f) \
                    and not closing_on_other:            # a close-up on its neighbour may show only part of it
                flagged.add((e["id"], "cut"))
                out.append(f"{e['id']} is cut by the frame at {f / timing.FPS:.1f} s: centre a camera key on its x ({e['x']})")
    out += empty_frames(scene, step=step)
    spots = [(b[0], b[2]) for e in els for b in [box_of(e) or _place_span(e)] if b]
    for k in cam:
        half = FRAME_W / 2 / max(0.3, k.get("zoom", 1.0))
        if spots and not any(x0 < k["x"] + half and x1 > k["x"] - half for x0, x1 in spots):
            out.append(f"the camera key at {k['at'] / timing.FPS:.1f} s (x {k['x']}) shows an empty street: point it at the place, "
                       "the people or the action")
    return out


EMPTY_LIMIT = 24                 # frames: the frame may show an empty street at most this long (a glide between two places)


def empty_frames(scene: dict, *, step: int = 6) -> list:
    """The frame shows something at every moment (Navin's D2 finding 8, "empty frames"): sampled every ``step`` frames on the
    renderer's own eased camera, a stretch longer than ``EMPTY_LIMIT`` frames in which no place, crowd, action, board, label,
    price tag or balance on screen at that time is in view, or the camera is still close on an action that has left, is
    reported once, with where the camera was."""
    layer = scene["layers"][0]["data"]
    els, cam, duration = layer["elements"], layer["camera"], scene["duration"]
    things = []
    for e in els:
        span = box_of(e) or _place_span(e)
        if span:
            t0, t1 = (0, duration) if e.get("kind") in WHOLE_PART_KINDS | set(PLACE_KINDS.values()) else _on(e, duration)
            things.append((span[0], span[2], t0, t1))
    if not things:
        return []
    acts = {e["id"]: _on(e, duration) for e in els if e.get("kind") == "action"}
    out, run = [], []
    for f in list(range(0, duration, step)) + [None]:
        empty = False
        if f is not None:
            c = cam_at(cam, f)
            half = FRAME_W / 2 / max(0.3, c["zoom"])
            empty = not any(t0 <= f < t1 and x0 < c["x"] + half - 60 and x1 > c["x"] - half + 60 for x0, x1, t0, t1 in things)
            active = next((k for k in reversed(cam) if k["at"] <= f), None)
            on = acts.get((active or {}).get("close_up"))
            if on and not on[0] <= f < on[1]:
                empty = True                     # a close-up on people who have gone shows nothing, whatever is at its edge
        if empty:
            run.append(f)
            continue
        if run and run[-1] - run[0] + step > EMPTY_LIMIT:
            c = cam_at(cam, run[0])
            out.append(f"the frame shows an empty street from {run[0] / timing.FPS:.1f} s to {(run[-1] + step) / timing.FPS:.1f} s "
                       f"(the camera at x {round(c['x'])}): keep the action there until the next comes (until_cue) or move the "
                       "camera to what is shown")
            break
        run = []
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
