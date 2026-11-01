"""Pick the videos of the generality proof by code (Task 046 Part D2 addendum, Navin, 2 November 2026, point 5).

"Besides Money v2 and v4, run the director with the narration locked on two other Money videos chosen by code (not v2, v4 or
v1), adding nothing by hand."

    python -B tools/task046d2_pick_videos.py --lesson <lesson_plan.json, a file or an https URL> [--count 2] [--not v1,v2,v4]

The rule: among the passed videos that are not excluded (and not the prerequisite video, kind ``prerequisites``), the ones whose
narration names the most words that the excluded videos never say (the things BIE has not been shown with yet: the strongest
test that only the named things are drawn); a tie goes to the shorter video (fewer beats, a quicker render), then to the id.
The words are the narration's content words (BIE's own stop lists and Hindi verb words left out, numbers left out).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))


def content_words(text: str) -> set:
    from bie.brain import soul
    from bie.brain.video import screen_text
    stop = soul.STOP | soul.HINDI_VERB_WORDS | screen_text.STOP
    words = re.findall(r"[a-z]+|[ऀ-ॿ]+", str(text or "").lower())
    return {w for w in words if len(w) > 2 and w not in stop}


def words_of(video: dict) -> set:
    out = set()
    for beat in video.get("beats") or []:
        out |= content_words(beat.get("say", ""))
    return out


def pick(lesson: dict, *, count: int = 2, exclude=("v1", "v2", "v4")) -> dict:
    videos = {v["video_id"]: v for v in lesson.get("videos") or []}
    kinds = {v.get("video_id"): v.get("kind", "") for v in (lesson.get("plan") or {}).get("videos") or []}
    seen = set()
    for vid in exclude:
        if vid in videos:
            seen |= words_of(videos[vid])
    rows = []
    for vid, video in videos.items():
        if vid in exclude or video.get("status") != "passed" or str(kinds.get(vid, "")).startswith("prereq"):
            continue
        new = words_of(video) - seen
        rows.append({"video_id": vid, "title": video.get("title", ""), "beats": len(video.get("beats") or []), "new_words": len(new),
                     "examples": sorted(new)[:12]})
    rows.sort(key=lambda r: (-r["new_words"], r["beats"], int(re.sub(r"\D", "", r["video_id"]) or 0)))
    return {"rule": "most narration words the excluded videos never say; then fewer beats; then the id",
            "excluded": list(exclude), "chosen": [r["video_id"] for r in rows[:count]], "ranking": rows}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lesson", required=True)
    ap.add_argument("--count", type=int, default=2)
    ap.add_argument("--not", dest="exclude", default="v1,v2,v4")
    a = ap.parse_args(argv)
    from run_brain import read_text
    from bie.brain import formats
    lesson = formats.accept("lesson_plan", json.loads(read_text(a.lesson)), where=a.lesson)
    out = pick(lesson, count=a.count, exclude=tuple(v.strip() for v in a.exclude.split(",") if v.strip()))
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
