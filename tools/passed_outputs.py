"""Export the passed work of a live run as a regression set, or check sets against today's code checks.

  python tools/passed_outputs.py export --run <run folder> --pdf <chapter PDF path or https URL> --out <set.json.gz>
         [--records <earlier run folder> ...] [--lesson <lesson run folder>]
  python tools/passed_outputs.py check <set.json.gz> [...]      (exit 1 when an earlier passed output now fails)

Seekh → code (CLAUDE.md): a new code check may not fail any output that passed before; the sets in
tests/fixtures/passed_outputs/ are checked by tests/test_task045_seekh.py on every pull request.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from bie.brain import regression  # noqa: E402


def page_blocks(pdf_bytes: bytes) -> dict:
    from bie.brain.pages import load_pages
    _, _, pages = load_pages(pdf_bytes, with_images=False)
    return {p.number: (True, [(b.id, b.text) for b in p.blocks]) for p in pages}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    ex = sub.add_parser("export")
    ex.add_argument("--run", type=Path, required=True)
    ex.add_argument("--pdf", required=True)
    ex.add_argument("--out", type=Path, required=True)
    ex.add_argument("--records", type=Path, nargs="*", default=[])
    ex.add_argument("--lesson", type=Path)
    ck = sub.add_parser("check")
    ck.add_argument("sets", type=Path, nargs="+")
    args = parser.parse_args(argv)
    if args.command == "export":
        from run_blind_test import read_source
        chapter = json.loads((args.run / "chapter_map.json").read_text(encoding="utf-8"))
        lesson = json.loads((args.lesson / "lesson_plan.json").read_text(encoding="utf-8")) if args.lesson else None
        passed = regression.export(chapter, page_blocks(read_source(args.pdf)), record_folders=[args.run, *args.records],
                                   lesson=lesson, source=args.run.name)
        regression.save(passed, args.out)
        print(json.dumps({"pages": len(passed["pages"]), "map": bool(passed["map"]),
                          "scripts": len((passed["lesson"] or {}).get("videos") or [])}))
        return 0
    failed = 0
    for path in args.sets:
        problems = regression.check(regression.load(path))
        failed += len(problems)
        print(json.dumps({"set": path.name, "problems": problems[:50], "count": len(problems)}, ensure_ascii=False))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
