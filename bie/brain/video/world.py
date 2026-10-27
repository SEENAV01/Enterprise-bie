"""World plan → scene spec for the L3 ``world_scene`` block (Task 046 Part C, from the economy kit of 27 October 2026).

Same contract as the canvas plans (``bie/brain/canvas.py``): the director names props, people, effects and camera moves,
each on a cue word ([beat_id, word] or [beat_id, "", fraction]); this code turns cues into frames through
``timing.py`` and checks the plan (unknown kinds, cue words not in their beat, camera keys out of order, a crowd step
that is not a number, the picture staying still too long). This is Navin's "C" level: a part that tells a story with
actors in a place is shown inside a small designed world; the kits a world can draw are listed in ``KITS`` (a part whose
place has no kit falls back to the canvas, and the place goes to the missing-capability log).
"""
from __future__ import annotations

import copy

from .. import canvas
from ..canvas import PlanError
from . import timing

KINDS = {"shop", "price_tag", "crowd", "coin_rain", "balance", "label", "pull_arrow", "title", "lamp", "foreground", "shopkeeper"}
# The places a world kit exists for: a story part set in one of these goes to world mode (C); the words are matched on the
# part's beats by the director (bie/brain/shots.py decides the mode, this module only draws).
KITS = {"shop": {"label": "a shop with buyers on a street", "words": ("दुकान", "दुकानदार", "shop", "shopkeeper", "बाज़ार", "बाजार",
                                                                   "market", "खरीदार", "buyer", "buyers", "ग्राहक", "customer")}}
CUE_KEYS = ("cue", "until_cue", "tilt_cue")


def compile_world(plan: dict, *, voice: dict | None = None, lead_in: float = timing.LEAD_IN):
    beats = plan["beats"]
    if not beats:
        raise PlanError("a world plan needs at least one beat")
    says = {b["beat_id"]: b["say"] for b in beats}
    sid = plan.get("id", "world")
    tl = timing.build(beats, [{"scene_id": sid, "beat_ids": [b["beat_id"] for b in beats]}], voice=voice, lead_in=lead_in)
    fps = tl[sid]["fps"]

    def frame_of(cue):
        return canvas.cue_frame(tl, sid, says, cue)

    changes = []
    els = []
    for n in copy.deepcopy(plan.get("elements") or []):
        if n.get("kind") not in KINDS:
            raise PlanError(f"{n.get('id', '?')}: unknown world element kind {n.get('kind')!r} (kinds: {', '.join(sorted(KINDS))})")
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
    if not any(e["kind"] == "shop" for e in els):
        raise PlanError("a world needs its place: add a shop element (the only kit so far)")
    cam = []
    for k in plan.get("camera") or []:
        f = frame_of(k["cue"])
        if cam and f < cam[-1]["at"]:
            raise PlanError("camera keys must be in time order")
        cam.append({"at": f, "x": k["x"], "y": k.get("y", 540), "zoom": k.get("zoom", 1.0), "frames": k.get("frames", 36)})
        changes.append(f)
    if not cam:
        raise PlanError("a world needs at least one camera key")
    duration = tl[sid]["duration"]
    pts = sorted(set(changes)) + [duration]
    still = max(b - a for a, b in zip(pts, pts[1:])) / fps
    problems = [f"the picture stays the same for {still:.1f} s (limit {canvas.MAX_STILL_S:.0f} s)"] if still > canvas.MAX_STILL_S else []
    data = {"world_width": plan.get("world_width", 5200), "elements": els, "camera": cam}
    scene = {"id": sid, "duration": duration, "camera": [{"at": 0}], "captions": canvas.captions_of(tl, sid, beats),
             "layers": [{"id": sid + "_world", "type": "block", "block": "world_scene", "at": 0, "box": {"x": 0, "y": 0, "w": 1, "h": 1}, "data": data}]}
    report = {"scene": sid, "seconds": round(duration / fps, 1), "elements": len(els), "camera_moves": len(cam),
              "longest_still_s": round(still, 1), "change_every_s": round(duration / fps / max(1, len(pts) - 1), 1), "problems": problems,
              "mode": "C", "level": "L3"}
    return scene, report


def kit_for(text: str) -> str:
    """The world kit whose place words appear in a part's text, or "" when no kit fits."""
    low = text.lower()
    for kit, info in KITS.items():
        if any(w.lower() in low for w in info["words"]):
            return kit
    return ""
