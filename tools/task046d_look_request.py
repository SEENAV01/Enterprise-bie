"""The LOOK-D1 request for one rendered video (Task 046 Part D1): one still per part (published by the render workflow under
``runs/<dest>/stills/<scene>.jpg``) and the teacher's point of that part, read by code from the canvas run's dikhane ki list.
The VM's look section (``tools/vm_look.py``, rule LOOK-D1) judges each still with the reviewer route under the cost guard
(Codex on the ChatGPT plan by default, Rs 0): does the picture alone hint at the point, and is it text only? Report only.

    python -B tools/task046d_look_request.py --canvas <canvas run folder> --video v4 --dest t046d-money-v4 --out request.json
        [--reviewer codex|google] [--rule look-d2|look-d1]

LOOK-D2 (Task 046 Part D2, the default): per beat its still (``stills/<scene>/<beat>.jpg``) and the items of the dikhane ki list;
the reviewer answers visible / happening per item and code computes the score.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain import look  # noqa: E402

RAW = "https://raw.githubusercontent.com/SEENAV01/Enterprise-bie/blindtest-results/runs"


def build_d2(canvas_dir: Path, video_id: str, dest: str, *, reviewer: str = "codex") -> dict:
    """LOOK-D2 (Task 046 Part D2): per part its beats (at most 8, spread over the part), each with the still the render workflow
    published at 65 % of the beat (``stills/<scene>/<beat>.jpg``), what it should show and the items the dikhane ki list names."""
    spec = json.loads((canvas_dir / "video_specs" / f"{video_id}.json").read_text(encoding="utf-8"))
    ideas = json.loads((canvas_dir / "visual_ideas" / f"{video_id}.json").read_text(encoding="utf-8"))
    by_part = {p["id"]: p for p in ideas.get("parts") or []}
    parts = []
    for scene in spec.get("scenes") or []:
        sid = str(scene.get("id") or "")
        if not sid or sid.endswith("_credits") or sid not in by_part:
            continue
        says = {}
        for c in scene.get("captions") or []:                 # a long beat's caption shows in pieces (CV-17): its words joined
            says[c.get("beat_id")] = f"{says.get(c.get('beat_id'), '')} {c.get('text', '')}".strip()
        beats = [b for b in by_part[sid].get("beats") or [] if b.get("beat_id") in says]
        if len(beats) > look.D2_MAX_BEATS:
            step = len(beats) / look.D2_MAX_BEATS
            beats = [beats[int(i * step)] for i in range(look.D2_MAX_BEATS)]
        rows = [{"beat_id": b["beat_id"], "say": says[b["beat_id"]][:240], "shows": b.get("shows", ""), "items": look.d2_items(b),
                 "frame": f"{RAW}/{dest}/stills/{sid}/{b['beat_id']}.jpg"} for b in beats]
        rows = [r for r in rows if r["items"]]
        if rows:
            parts.append({"id": sid, "beats": rows})
    return {"schema": "bie.look-request/1", "rule": look.D2_RULE, "reviewer": reviewer, "video": video_id, "dest": dest,
            "parts": parts[:40]}


def build(canvas_dir: Path, video_id: str, dest: str, *, reviewer: str = "codex") -> dict:
    spec = json.loads((canvas_dir / "video_specs" / f"{video_id}.json").read_text(encoding="utf-8"))
    ideas_path = canvas_dir / "visual_ideas" / f"{video_id}.json"
    ideas = json.loads(ideas_path.read_text(encoding="utf-8")) if ideas_path.exists() else {"parts": []}
    by_part = {p["id"]: p for p in ideas.get("parts") or []}
    parts = []
    for scene in spec.get("scenes") or []:
        sid = str(scene.get("id") or "")
        if not sid or sid.endswith("_credits"):
            continue
        p = by_part.get(sid) or {}
        points = [b.get("idea", "") for b in p.get("beats") or [] if b.get("idea")]
        point = "; ".join(points[:3]) or " ".join(c.get("text", "") for c in (scene.get("captions") or [])[:2])[:240]
        parts.append({"id": sid, "point": point[:400] or sid, "frame": f"{RAW}/{dest}/stills/{sid}.jpg"})
    return {"schema": "bie.look-request/1", "rule": look.D1_RULE, "reviewer": reviewer, "video": video_id, "dest": dest,
            "parts": parts[:40]}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--canvas", required=True, type=Path)
    parser.add_argument("--video", required=True)
    parser.add_argument("--dest", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--reviewer", choices=("codex", "google"), default="codex")
    parser.add_argument("--rule", choices=("look-d1", "look-d2"), default="look-d2")
    args = parser.parse_args(argv)
    request = (build_d2 if args.rule == "look-d2" else build)(args.canvas, args.video, args.dest, reviewer=args.reviewer)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(request, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{args.out}: {len(request['parts'])} parts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
