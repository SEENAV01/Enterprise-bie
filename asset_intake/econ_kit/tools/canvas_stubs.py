"""BIE lesson plan video → one canvas plan stub per script part (the AI director fills the ``nodes``).

Groups beats into parts exactly as ``bie/brain/shots.py`` does (a hook before the first part belongs to that part; a
closing beat without a part stays with the last part), so the canvas scenes line up with the code director's scenes.

    python canvas_stubs.py lesson_plan.json VIDEO_ID OUT_DIR
"""
import json
import os
import sys


def parts(video: dict):
    scenes, current = [], None
    for beat in video.get("beats") or []:
        pid = beat.get("part_id") or ""
        if current is None:
            current = {"part_id": pid, "beats": [beat]}
            scenes.append(current)
        elif not current["part_id"] and pid:
            current["part_id"] = pid
            current["beats"].append(beat)
        elif pid and pid != current["part_id"]:
            current = {"part_id": pid, "beats": [beat]}
            scenes.append(current)
        else:
            current["beats"].append(beat)
    return scenes


def stubs(video: dict):
    out = []
    for i, sc in enumerate(parts(video), 1):
        out.append({"id": f"{video.get('video_id', 'v')}_s{i}", "part_id": sc["part_id"], "theme": "paper", "grid": [12, 8],
                    "beats": [{"beat_id": b["beat_id"], "say": b["say"]} for b in sc["beats"]],
                    "covers_item_ids": sorted({i for b in sc["beats"] for i in (b.get("covers_item_ids") or [])}),
                    "on_screen_hints": [b.get("on_screen") for b in sc["beats"] if b.get("on_screen")],
                    "nodes": []})
    return out


if __name__ == "__main__":
    plan = json.load(open(sys.argv[1], encoding="utf-8"))
    video = next(v for v in plan["videos"] if v.get("video_id") == sys.argv[2])
    os.makedirs(sys.argv[3], exist_ok=True)
    for s in stubs(video):
        json.dump(s, open(os.path.join(sys.argv[3], s["id"] + ".stub.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(s["id"], s["part_id"], len(s["beats"]), "beats")
