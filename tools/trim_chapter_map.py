"""Trim a passed chapter map to the items some videos actually teach (Phase 1, part F; code does the trim, never a hand).

    python -B tools/trim_chapter_map.py --map <chapter_map.json path or URL> --lesson <lesson_plan.json path or URL> \
        --videos v4[,v2] --out <folder>

Writes ``<out>/chapter_map.json``: the same map with only the items the named videos' beats cover (plus their
concepts, trimmed to those items) and a ``TRIM.md`` naming the source, the videos and the counts, so a partial run
(one video's notes and game) carries a map of its own scope instead of the whole chapter. The trimmed map still
validates as ``bie.brain.chapter-map/2`` and says where it came from.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain import formats  # noqa: E402


def read_json(where: str) -> dict:
    if where.startswith("https://"):
        with urllib.request.urlopen(where, timeout=60) as response:   # noqa: S310 (https only)
            return json.loads(response.read().decode("utf-8"))
    return json.loads(Path(where).read_text(encoding="utf-8"))


def trim(chapter: dict, lesson: dict, videos: list) -> dict:
    wanted = set()
    for video in lesson.get("videos") or []:
        if video["video_id"] in videos:
            for beat in video.get("beats") or []:
                wanted.update(beat.get("covers_item_ids") or [])
    if not wanted:
        raise SystemExit(f"no beats cover anything for {', '.join(videos)}")
    out = dict(chapter)
    out["items"] = {iid: item for iid, item in chapter["items"].items() if iid in wanted}
    the_map = dict(chapter["map"])
    concepts = []
    for c in the_map.get("concepts") or []:
        ids = [i for i in c["item_ids"] if i in wanted]
        if ids:
            concepts.append(dict(c, item_ids=ids))
    the_map["concepts"] = concepts
    out["map"] = the_map
    out["pages"] = [p for p in chapter.get("pages") or []
                    if any(chapter["items"].get(i, {}).get("page") == p.get("page") for i in wanted)] or chapter.get("pages") or []
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--map", required=True)
    ap.add_argument("--lesson", required=True)
    ap.add_argument("--videos", required=True)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args(argv)
    videos = [v.strip() for v in a.videos.split(",") if v.strip()]
    chapter = formats.accept("chapter_map", read_json(a.map), where=a.map)
    lesson = formats.accept("lesson_plan", read_json(a.lesson), where=a.lesson)
    out = trim(chapter, lesson, videos)
    formats.check("chapter_map", out, where="trimmed chapter_map.json")
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "chapter_map.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    (a.out / "TRIM.md").write_text(
        f"# Trimmed chapter map (by tools/trim_chapter_map.py, never a hand)\n\n"
        f"- Source map: {a.map}\n- Lesson: {a.lesson}\n- Videos: {', '.join(videos)}\n"
        f"- Items: {len(out['items'])} of {len(chapter['items'])}; concepts: {len(out['map']['concepts'])} of "
        f"{len(chapter['map']['concepts'])}.\n", encoding="utf-8")
    print(f"trimmed map: {len(out['items'])} items, {len(out['map']['concepts'])} concepts -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
