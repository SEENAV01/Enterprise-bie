"""Task 044 offline test lane: the Codex maker route (fake codex executable: success, schema error, plan-limit
stop, sign-in missing), its cost-guard preflight and the private-machine job runner — plus the Task 043, 039 and
038 lanes it builds on. No network, no keys, no ChatGPT sign-in.

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

# the VM runner's image and look sections (Task 046 one-shot; PR #77 added the file but no lane ran it)
NEW = ("tests/test_task044_codex.py", "tests/test_task046_vm_image.py")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    rows = [run_file(path) for path in NEW + TASK043 + TASK039 + TASK038 + AFFECTED]
    totals = {key: sum(row[key] for row in rows) for key in ("tests", "failures", "errors", "skips")}
    passed = totals["failures"] == totals["errors"] == 0 and all(row["tests"] > 0 for row in rows)
    summary = {"lane": "task044", "passed": passed, **totals, "files": len(rows), "evidence_kind": "TECHNICAL_TEST",
               "product_accepted": False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"summary": summary, "results": rows}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
