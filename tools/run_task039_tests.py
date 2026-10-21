"""Task 039 offline test lane: image parts in the gateway, the vision rulebook, the section runner and
Section 1 (understanding the book), plus the Task 038 gateway tests they build on. No network, no keys.

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

NEW = ("tests/test_task039_brain.py",)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    rows = [run_file(path) for path in NEW + TASK038 + AFFECTED]
    totals = {key: sum(row[key] for row in rows) for key in ("tests", "failures", "errors", "skips")}
    passed = totals["failures"] == totals["errors"] == 0 and all(row["tests"] > 0 for row in rows)
    summary = {"lane": "task039", "passed": passed, **totals, "files": len(rows), "evidence_kind": "TECHNICAL_TEST",
               "product_accepted": False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"summary": summary, "results": rows}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
