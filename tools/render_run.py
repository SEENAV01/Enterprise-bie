"""Re-render the readable pages of a finished brain run with the current code.

  python tools/render_run.py <run folder> [--out <folder>]

Reads ``chapter_map.json`` (Section 1) and ``lesson_plan.json`` (Section 2) from the run folder and writes MAP.md and
PAGES.md, SCRIPT.md and scripts/<video id>.md with today's renderers, by default into ``<run folder>/readable/`` so
the run's own outputs stay as they were written. Nothing is sent to any model; the pages only show what BIE made.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain import lesson as lesson_module  # noqa: E402
from bie.brain import understanding  # noqa: E402


def render(run: Path, out: Path) -> list:
    out.mkdir(parents=True, exist_ok=True)
    written = []
    chapter_path = run / "chapter_map.json"
    if chapter_path.exists():
        chapter = json.loads(chapter_path.read_text(encoding="utf-8"))
        chapter.setdefault("quality", understanding.quality(chapter))
        (out / "MAP.md").write_text(understanding.render_markdown(chapter), encoding="utf-8")
        (out / "PAGES.md").write_text(understanding.render_pages(chapter), encoding="utf-8")
        written += ["MAP.md", "PAGES.md"]
    lesson_path = run / "lesson_plan.json"
    if lesson_path.exists():
        lesson = json.loads(lesson_path.read_text(encoding="utf-8"))
        for video in lesson.get("videos") or []:
            video.setdefault("card_parts", [])
            video.setdefault("parts", [])
        lesson_module.write_pages(lesson, out)
        written += ["SCRIPT.md"] + [f"scripts/{v['video_id']}.md" for v in lesson.get("videos") or []]
    return written


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    written = render(args.run, args.out or args.run / "readable")
    if not written:
        raise SystemExit("NOTHING_TO_RENDER: no chapter_map.json or lesson_plan.json in " + str(args.run))
    print(json.dumps({"written": written}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
