"""Lock explanations after Navin's verdict (Task 045d; Navin, 24 October 2026).

  python tools/lock_explanations.py --run <run folder or https URL> --items p003-i2,p003-i5 --by "Navin, 25 October 2026"
  python tools/lock_explanations.py --show "absorptive surface"

Copies the unpack (terms with their plain meaning and everyday image, the why chain) of the named items of a passed run's
``chapter_map.json`` into ``bie/brain/rulebook/explanations.json`` as locked entries, with the run id and who locked them;
the file's version is bumped and the change is listed. Later runs reuse a locked explanation for the same term in any
book (``bie/brain/explanations.py``). Only Navin's verdict locks: Claude runs this tool after his yes on named items,
never on its own. The change is a reviewed PR like any rulebook change.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from bie.brain import explanations  # noqa: E402
from run_brain import read_text  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run", help="run folder or https URL with chapter_map.json")
    parser.add_argument("--items", default="", help="item ids to lock, comma separated (their unpack must have passed)")
    parser.add_argument("--by", default="", help="who locked and when, for example 'Navin, 25 October 2026'")
    parser.add_argument("--path", default=str(explanations.PATH))
    parser.add_argument("--show", default="", help="print the locked entries whose term appears in this text, then exit")
    args = parser.parse_args(argv)
    if args.show:
        for entry in explanations.load(args.path).lookup(args.show):
            print(entry.line())
        return 0
    if not (args.run and args.items and args.by):
        parser.error("--run, --items and --by are required to lock")
    chapter = json.loads(read_text(args.run.rstrip("/") + "/chapter_map.json"))
    ids = [i.strip() for i in args.items.split(",") if i.strip()]
    missing = [i for i in ids if i not in chapter["items"]]
    if missing:
        print("ITEMS_NOT_IN_MAP:" + ",".join(missing), file=sys.stderr)
        return 2
    empty = [i for i in ids if not (chapter["items"][i].get("unpack") or {}).get("terms")]
    if empty:
        print("ITEMS_WITHOUT_TERMS:" + ",".join(empty) + " (only an unpack with terms can be locked)", file=sys.stderr)
        return 2
    run_id = args.run.rstrip("/").rsplit("/", 1)[-1]
    written = explanations.lock_from_items(chapter, ids, by=args.by, run=run_id, path=args.path)
    for entry in written:
        print(f"locked: {entry['term']} ({entry['key']}) from {entry['from_run']}")
    print(f"{len(written)} entries written to {args.path} (version {explanations.load(args.path).version})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
