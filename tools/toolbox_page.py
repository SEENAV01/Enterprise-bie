"""Write the readable toolbox page (Task 046a).

    python tools/toolbox_page.py [--results <demo out>/RESULTS.json | <demo out>] [--missing <log.jsonl>] [--out docs/toolbox/TOOLBOX.md]

Given the demo folder instead of RESULTS.json, the page reads every <demo>/receipt.json in it (so demos rendered in
several runs with --only make one page).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.toolbox import page, registry  # noqa: E402
from bie.toolbox.resolver import MissingLog  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--results", type=Path, nargs="*", default=[], help="RESULTS.json files or demo folders (several batches)")
    parser.add_argument("--missing", type=Path)
    parser.add_argument("--note", default="")
    parser.add_argument("--out", type=Path, default=ROOT / "docs" / "toolbox" / "TOOLBOX.md")
    args = parser.parse_args(argv)
    rows = []
    for source in args.results:
        if source.is_dir():
            rows += [json.loads(p.read_text(encoding="utf-8")) for p in sorted(source.glob("*/receipt.json"))]
        else:
            rows += json.loads(source.read_text(encoding="utf-8")).get("results", [])
    results = None
    if rows:
        rows.sort(key=lambda r: (r.get("batch") or 0, r["demo"]))
        results = {"schema": "bie.toolbox.demo-results/1", "batch": ", ".join(sorted({str(r.get("batch")) for r in rows})),
                   "demos": len(rows), "passed": all(r.get("passed") for r in rows), "results": rows}
    missing = MissingLog(args.missing).summary() if args.missing else None
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(page.render_markdown(registry.load(), results, missing_log=missing, clips_note=args.note), encoding="utf-8")
    print(args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
