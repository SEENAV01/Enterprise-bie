"""World plan → scene spec for the L3 ``world_scene`` block (asset intake, economy batch, 27 Oct 2026).

Same contract as the canvas plans: the director names props, people, effects and camera moves, each on a cue word
([beat_id, word] or [beat_id, "", fraction]); this code turns cues into frames through bie/brain/video/timing.py and
checks the plan (unknown kinds, cue words not in their beat, camera keys out of order, a crowd step that is not a
number, the picture staying still too long).

    python world_plan.py PLAN.json --out SPEC.json
"""
from __future__ import annotations

import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import econ_canvas as ec  # noqa: E402  (also patches timing._norm for the danda)
from econ_canvas import PlanError, timing  # noqa: E402

KINDS = {"shop", "price_tag", "crowd", "coin_rain", "balance", "label", "pull_arrow", "title", "lamp", "foreground", "shopkeeper"}
CUE_KEYS = ("cue", "until_cue", "tilt_cue")


def compile_world(plan: dict):
    beats = plan["beats"]
    says = {b["beat_id"]: b["say"] for b in beats}
    sid = plan.get("id", "world")
    tl = timing.build(beats, [{"scene_id": sid, "beat_ids": [b["beat_id"] for b in beats]}])
    fps = tl[sid]["fps"]

    def frame_of(cue):
        bid, word = cue[0], cue[1]
        if bid not in says:
            raise PlanError(f"cue names an unknown beat {bid!r}")
        if word:
            if f" {timing._norm(word).strip()} " not in f" {timing._norm(says[bid])} ":
                raise PlanError(f"cue word {word!r} is not in beat {bid}: {says[bid][:80]!r}")
            return timing.cue_frame(tl, sid, bid, word, says)
        start, length = tl[sid]["beats"][bid]
        return start + round(length * (cue[2] if len(cue) > 2 else 0.0))

    changes = []
    els = []
    for n in copy.deepcopy(plan["elements"]):
        if n["kind"] not in KINDS:
            raise PlanError(f"unknown world element kind {n['kind']!r}")
        if "cue" in n:
            n["at"] = frame_of(n.pop("cue")); changes.append(n["at"])
        if "until_cue" in n:
            n["until"] = frame_of(n.pop("until_cue")); changes.append(n["until"])
        if "tilt_cue" in n:
            n["tilt_at"] = frame_of(n.pop("tilt_cue")); changes.append(n["tilt_at"])
        for key in ("steps", "packets"):
            for st in n.get(key, []):
                st["at"] = frame_of(st.pop("cue")); changes.append(st["at"])
                if "n" in st and not isinstance(st["n"], int):
                    raise PlanError(f"{n['id']}: a step count must be a whole number")
        for key in ("lift", "carry"):
            if key in n:
                n[key]["at"] = frame_of(n[key].pop("cue")); changes.append(n[key]["at"])
        els.append(n)
    cam = []
    for k in plan["camera"]:
        f = frame_of(k["cue"])
        if cam and f < cam[-1]["at"]:
            raise PlanError("camera keys must be in time order")
        cam.append({"at": f, "x": k["x"], "y": k.get("y", 540), "zoom": k.get("zoom", 1.0), "frames": k.get("frames", 36)})
        changes.append(f)
    duration = tl[sid]["duration"]
    pts = sorted(set(changes)) + [duration]
    still = max(b - a for a, b in zip(pts, pts[1:])) / fps
    problems = [f"the picture stays the same for {still:.1f} s (limit {ec.MAX_STILL_S} s)"] if still > ec.MAX_STILL_S else []
    subs = []
    for b in beats:
        start, length = tl[sid]["beats"][b["beat_id"]]
        subs.append({"at": start, "until": start + length, "text": b.get("caption", b["say"])})
    data = {"world_width": plan.get("world_width", 5200), "elements": els, "camera": cam, "subtitles": subs}
    scene = {"id": sid, "duration": duration, "camera": [{"at": 0}], "captions": [],
             "layers": [{"id": sid + "_world", "type": "block", "block": "world_scene", "at": 0, "box": {"x": 0, "y": 0, "w": 1, "h": 1}, "data": data}]}
    report = {"scene": sid, "seconds": round(duration / fps, 1), "elements": len(els), "camera_moves": len(cam),
              "longest_still_s": round(still, 1), "change_every_s": round(duration / fps / max(1, len(pts) - 1), 1), "problems": problems}
    return scene, report


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("plans", nargs="+")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    scenes, reports = [], []
    for p in a.plans:
        s, r = compile_world(json.load(open(p, encoding="utf-8")))
        scenes.append(s)
        reports.append(r)
    json.dump({"fps": timing.FPS, "width": 1920, "height": 1080, "captions": False, "scenes": scenes}, open(a.out, "w", encoding="utf-8"),
              ensure_ascii=False)
    print(json.dumps(reports, ensure_ascii=False, indent=1))
