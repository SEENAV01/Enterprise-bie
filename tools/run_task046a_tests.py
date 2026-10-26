"""Task 046a test lane: the toolbox registry, resolver, sources, page, the lesson licence gate of Task 046a-L and the Task 046
shot-list director (core, standard library) and one test per wrapper with the real libraries (wrappers; needs every toolbox extra, Blender and
Manim). No network, no keys, no money.

    python -B tools/run_task046a_tests.py --lane core|wrappers|all --output <receipt.json>

A lane passes only with no failure, no error and no skip (a skipped wrapper would hide a missing library).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from run_task038_tests import run_file  # noqa: E402

# The wrappers file sits in tests/toolbox/, which the canonical gate does not discover: its libraries are toolbox extras.
LANES = {"core": ("tests/test_task046a_toolbox.py", "tests/test_task046a_licence.py", "tests/test_task046_shots.py",
                  "tests/test_task046_blocks.py", "tests/test_task046_oneshot.py"),
         "wrappers": ("tests/toolbox/test_wrappers.py", "tests/toolbox/test_task046_frames.py")}
LANES["all"] = LANES["core"] + LANES["wrappers"]


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--lane", choices=sorted(LANES), default="core")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    rows = [run_file(path) for path in LANES[args.lane]]
    totals = {key: sum(row[key] for row in rows) for key in ("tests", "failures", "errors", "skips")}
    passed = totals["failures"] == totals["errors"] == totals["skips"] == 0 and all(row["tests"] > 0 for row in rows)
    summary = {"lane": "task046a-" + args.lane, "passed": passed, **totals, "files": len(rows), "evidence_kind": "TECHNICAL_TEST",
               "product_accepted": False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"summary": summary, "results": rows}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
