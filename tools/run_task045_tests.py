"""Task 045 offline test lane: content-type detection, the naksha, task cards, the old KI, PR, RE and PED engines as
code checks, Sections 1 and 2 on the card (fake AI) and the seekh → BIE sets (earlier passed outputs re-checked with
today's checks) — plus the Task 044, 043, 039 and 038 lanes they build on. No network, no keys, no money.

Writes a producer-lane receipt ({"summary", "results"}) that tools/ci_failure_annotation.py can read.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from run_task038_tests import AFFECTED, NEW as TASK038, run_file  # noqa: E402
from run_task039_tests import NEW as TASK039  # noqa: E402
from run_task043_tests import NEW as TASK043  # noqa: E402
from run_task044_tests import NEW as TASK044  # noqa: E402

NEW = ("tests/test_task045_cards.py", "tests/test_task045_seekh.py", "tests/test_task045d_soul.py",
       "tests/test_task045_free_reviewer.py", "tests/test_task046c_real_world.py")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    rows = [run_file(path) for path in NEW + TASK044 + TASK043 + TASK039 + TASK038 + AFFECTED]
    totals = {key: sum(row[key] for row in rows) for key in ("tests", "failures", "errors", "skips")}
    passed = totals["failures"] == totals["errors"] == 0 and all(row["tests"] > 0 for row in rows)
    summary = {"lane": "task045", "passed": passed, **totals, "files": len(rows), "evidence_kind": "TECHNICAL_TEST",
               "product_accepted": False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"summary": summary, "results": rows}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
