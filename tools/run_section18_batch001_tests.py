from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RecordedResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = {}

    def startTest(self, test):
        super().startTest(test)
        self.records.setdefault(test.id(), {"test_id": test.id(), "status": "RUNNING"})

    def _row(self, test):
        return self.records.setdefault(test.id(), {"test_id": test.id(), "status": "RUNNING"})

    def addSuccess(self, test):
        super().addSuccess(test)
        self._row(test)["status"] = "PASS"

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._row(test)["status"] = "FAIL"

    def addError(self, test, err):
        super().addError(test, err)
        self._row(test)["status"] = "ERROR"

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self._row(test)["status"] = "SKIP"
        self._row(test)["reason"] = reason

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None:
            self._row(test)["status"] = "FAIL"


def inventory():
    rows = {}
    for root in ("bie/app_product", "tests/section18", "docs/section18", "metadata/section18"):
        base = ROOT / root
        for path in sorted(base.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                rel = path.relative_to(ROOT).as_posix()
                rows[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    output = Path(args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=False)
    before = inventory()
    start = time.time()
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests/section18"), pattern="test_app_*.py", top_level_dir=str(ROOT))
    with (output / "TEST_RESULT.txt").open("w", encoding="utf-8", buffering=1) as stream:
        runner = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=RecordedResult)
        result = runner.run(suite)
    records = sorted(result.records.values(), key=lambda x: x["test_id"])
    after = inventory()
    report = {
        "schema_version": "bie.section18.batch001-test-result/1",
        "python": sys.version,
        "platform": platform.platform(),
        "tests_run": result.testsRun,
        "unique_test_ids": len(records),
        "passed": sum(x["status"] == "PASS" for x in records),
        "failed": sum(x["status"] == "FAIL" for x in records),
        "errors": sum(x["status"] == "ERROR" for x in records),
        "skipped": sum(x["status"] == "SKIP" for x in records),
        "duration_seconds": time.time() - start,
        "records": records,
        "inventory_sha256": hashlib.sha256(
            json.dumps(before, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "source_changed_during_tests": before != after,
        "all_passed": result.wasSuccessful() and not result.skipped and before == after,
        "section_complete": False,
        "product_accepted": False,
    }
    (output / "TEST_RESULT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (output / "INVENTORY.json").write_text(json.dumps(before, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in (
        "tests_run", "passed", "failed", "errors", "skipped", "all_passed", "inventory_sha256"
    )}, indent=2))
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
