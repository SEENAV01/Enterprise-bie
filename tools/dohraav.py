"""Dohraav (restating) measure: how much of a run's script only restates the book (Task 045d; Navin, 24 October 2026).

  python tools/dohraav.py <run folder or https URL> [<run folder> ...] [--json]

Reads each folder's ``chapter_map.json`` and ``lesson_plan.json`` (a folder without a lesson plan gives the chapter
map for the folders after it, so a lesson run may follow the understanding run it was planned from) and reports,
per video and in all: the beats judged (explaining beats that cover items), how many only restate the book (60% or
more of their English content words are the covered items' own, 6 or more such words, and no yaani, why, example or
contrast marker), the share, how many are opened (carry a marker), clipped note-like sentences, topics that open
without a question and duplicate recaps. The same measure runs inside the script check (``bie/brain/soul.py``), so
the number before and after a change is comparable. Nothing is sent to any model.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from bie.brain import soul  # noqa: E402
from run_brain import read_text  # noqa: E402


def _load(base: str, name: str):
    try:
        return json.loads(read_text(base.rstrip("/") + "/" + name))
    except (OSError, ValueError):
        return None


def measure(chapter: dict, lesson: dict) -> dict:
    """{videos: [{video, judged, restating, share, opened, clipped, no_question, duplicate_recaps}], total: {...}}."""
    items = chapter["items"]
    rows, total = [], {"beats": 0, "judged": 0, "restating": 0, "opened": 0, "clipped": 0, "no_question": 0, "duplicate_recaps": 0}
    for video in lesson["videos"]:
        beats = video.get("beats") or []
        share = soul.dohraav_share(beats, items)
        row = {"video": video["video_id"], "status": video.get("status", ""), "beats": share["beats"], "judged": share["judged"],
               "restating": share["restating"], "share": share["share"], "opened": share["opened"], "opened_share": share["opened_share"],
               "clipped": sum(len(soul.clipped_sentences(b.get("say", ""))) for b in beats),
               "no_question": len(soul.opening_problems(beats, video.get("card_parts") or [])),
               "duplicate_recaps": len(soul.recap_problems(beats))}
        rows.append(row)
        for key in total:
            total[key] += row[key]
    judged = max(total["judged"], 1)
    total.update(videos=len(rows), share=round(total["restating"] / judged, 3), opened_share=round(total["opened"] / judged, 3))
    return {"videos": rows, "total": total}


def render(result: dict) -> str:
    lines = ["video | status | beats | judged | restating | share | opened | clipped | no question | duplicate recaps",
             "--- | --- | --- | --- | --- | --- | --- | --- | --- | ---"]
    for r in result["videos"]:
        lines.append(f"{r['video']} | {r['status']} | {r['beats']} | {r['judged']} | {r['restating']} | {r['share']:.0%} | {r['opened']} | "
                     f"{r['clipped']} | {r['no_question']} | {r['duplicate_recaps']}")
    t = result["total"]
    lines.append(f"all {t['videos']} | | {t['beats']} | {t['judged']} | {t['restating']} | {t['share']:.0%} | {t['opened']} | {t['clipped']} | "
                 f"{t['no_question']} | {t['duplicate_recaps']}")
    lines.append(f"\nDohraav: {t['restating']} of {t['judged']} judged beats ({t['share']:.1%}) only restate the book; "
                 f"{t['opened']} ({t['opened_share']:.1%}) carry an opening marker (yaani, why, example, contrast).")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("runs", nargs="+", help="run folders or https URLs, in order")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    chapter, results = None, {}
    for run in args.runs:
        chapter = _load(run, "chapter_map.json") or chapter
        lesson = _load(run, "lesson_plan.json")
        if lesson is None:
            continue
        if chapter is None:
            print(f"{run}: no chapter_map.json here or in an earlier folder", file=sys.stderr)
            return 2
        results[run] = measure(chapter, lesson)
    if not results:
        print("no lesson_plan.json in the folders given", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=1))
    else:
        for run, result in results.items():
            print(f"## {run}\n\n{render(result)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
