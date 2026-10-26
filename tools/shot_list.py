"""Shot lists by code for the passed scripts of a lesson run (Task 046, Part A): the offline proof on v3.

  python -B tools/shot_list.py --from-run <folder or https URL with chapter_map.json and lesson_plan.json> [--videos v3] --out <dir>

Writes <out>/shots/<video>.json, <out>/SHOTS.md and <out>/shots.json, and prints the level split, the render verdict and
every W-01 hit per video. No AI call, no network beyond fetching the two run files from a URL.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from bie.brain import shots  # noqa: E402
from bie.brain.understanding import Course  # noqa: E402
from run_brain import read_text  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-run", required=True)
    parser.add_argument("--videos", default="")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    base = args.from_run.rstrip("/") + "/"
    chapter = json.loads(read_text(base + "chapter_map.json"))
    lesson = json.loads(read_text(base + "lesson_plan.json"))
    course = Course(**{k: v for k, v in (chapter.get("course") or lesson.get("course") or {}).items()
                       if k in ("title", "subject", "learners", "exam", "language", "level")})
    wanted = [v.strip() for v in args.videos.split(",") if v.strip()] or None
    summary = shots.run_shots(chapter, lesson, course, args.out, video_ids=wanted)
    for video in summary["videos"]:
        if video.get("status") == "skipped":
            print(f"{video['video_id']}: skipped ({video['why']})")
            continue
        split = ", ".join(f"{lvl} {v['share']:.1%}" for lvl, v in video["level_split"].items())
        pace = video["pace"]
        print(f"{video['video_id']}: {video['shots']} shots, {video['seconds']} s; main level {video['main_level']}; {split}; L3+ "
              f"{video['l3_plus_share']:.1%}; a visual change every {pace['seconds_per_change']} s ({pace['camera_moves_added']} camera moves added) "
              f"→ {video['status']}; W-01 hits {video['wording_hits']}; advisory {video['advisory']}")
        for p in video["blocking"]:
            print("  blocking:", p)
    chapter = summary.get("chapter") or {}
    if chapter:
        print(f"chapter: {chapter['l3_plus_videos']} of {chapter['videos']} videos with main level L3 or above ({chapter['share']:.0%}; "
              f"target {chapter['target'][0]:.0%}-{chapter['target'][1]:.0%}, " + ("met" if chapter["meets_target"] else "not met") + ")")
    print(f"written: {args.out / 'SHOTS.md'}")
    return 0 if all(v.get("status") != "blocked" for v in summary["videos"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
