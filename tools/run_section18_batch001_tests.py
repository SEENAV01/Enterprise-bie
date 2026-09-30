#!/usr/bin/env python3
"""Run Section 18 Batch 001 tests plus affected inherited API regressions."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_TOTAL = 133
SUITES = (
    ("section18-run-source", [sys.executable, "-B", "-m", "unittest", "-v", "tests.section18.test_run_and_source"], 13),
    ("section18-status-timeline-failure", [sys.executable, "-B", "-m", "unittest", "-v", "tests.section18.test_status_timeline_failure"], 10),
    ("section18-controls", [sys.executable, "-B", "-m", "unittest", "-v", "tests.section18.test_controls"], 13),
    ("section18-graphs", [sys.executable, "-B", "-m", "unittest", "-v", "tests.section18.test_graph_views"], 12),
    ("section18-web-contract", [sys.executable, "-B", "-m", "unittest", "-v", "tests.section18.test_web_contract"], 12),
    ("section18-metadata", [sys.executable, "-B", "-m", "unittest", "-v", "tests.section18.test_batch001_metadata"], 7),
    ("inherited-pdf-api", [sys.executable, "-B", "tests/productization/api/test_pdf_inspection_api.py"], 22),
    ("inherited-persistent-jobs", [sys.executable, "-B", "tests/productization/api/test_persistent_pdf_jobs.py"], 44),
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def inventory() -> dict[str, str]:
    roots = [
        ROOT / "bie" / "app_product",
        ROOT / "apps" / "api",
        ROOT / "apps" / "web" / "section18",
        ROOT / "tests" / "section18",
        ROOT / "metadata" / "section18",
        ROOT / "docs" / "section18",
    ]
    explicit = [
        ROOT / "scripts" / "run_bie_operator_worker.py",
        ROOT / "tools" / "run_section18_batch001_tests.py",
        ROOT / "tools" / "run_section18_batch001_browser_smoke.py",
        ROOT / "tools" / "package_section18_batch001.py",
        ROOT / "tools" / "verify_section18_batch001_package.py",
    ]
    result: dict[str, str] = {}
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                result[path.relative_to(ROOT).as_posix()] = sha256_bytes(path.read_bytes())
    for path in explicit:
        if path.is_file():
            result[path.relative_to(ROOT).as_posix()] = sha256_bytes(path.read_bytes())
    return dict(sorted(result.items()))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    out = Path(args.output_dir).resolve()
    out.mkdir(parents=True, exist_ok=False)

    before = inventory()
    records = []
    all_ok = True
    total = 0
    for suite_id, argv, expected in SUITES:
        result = subprocess.run(
            argv,
            cwd=ROOT,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        combined = (result.stdout or "") + (result.stderr or "")
        (out / f"{suite_id}.log").write_text(combined, encoding="utf-8")
        matches = re.findall(r"Ran\s+(\d+)\s+tests?", combined)
        observed = int(matches[-1]) if matches else -1
        skipped = bool(re.search(r"skipped=\d+", combined))
        passed = result.returncode == 0 and observed == expected and not skipped
        records.append({
            "suite_id": suite_id,
            "argv": argv,
            "expected_tests": expected,
            "observed_tests": observed,
            "exit_code": result.returncode,
            "skipped_reported": skipped,
            "log_sha256": sha256_bytes(combined.encode("utf-8")),
            "passed": passed,
        })
        total += max(observed, 0)
        all_ok = all_ok and passed

    after = inventory()
    source_changed = before != after
    all_ok = all_ok and total == EXPECTED_TOTAL and not source_changed
    report = {
        "schema_version": "bie.section18.batch001.tests/1",
        "baseline_main_sha": "47cafba8975061555764c3c579ae6daad696ae64",
        "head_sha": os.environ.get("GITHUB_SHA") or os.popen("git rev-parse HEAD").read().strip(),
        "expected_total_tests": EXPECTED_TOTAL,
        "observed_total_tests": total,
        "suite_count": len(records),
        "suites": records,
        "source_changed_during_tests": source_changed,
        "candidate_inventory_sha256": sha256_bytes(
            json.dumps(before, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ),
        "all_passed": all_ok,
        "product_accepted": False,
        "section_complete": False,
        "task028": "PAUSED_UNCHANGED",
        "counting_note": "133 is 67 Batch001 task/metadata tests plus 66 affected inherited API/job tests; browser smoke is separate and is not added to this count.",
    }
    (out / "TEST_RESULT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (out / "CANDIDATE_INVENTORY.json").write_text(json.dumps(before, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
