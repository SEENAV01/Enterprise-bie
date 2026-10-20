"""Task 038 offline test lane: live-provider clients, gateway and blind-test harness (no network, no keys).

Writes a producer-lane receipt ({"summary", "results"}) that tools/ci_failure_annotation.py can read.
"""
from __future__ import annotations

import argparse
import importlib.util
import io
import json
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

NEW = (
    "tests/test_task038_live_providers.py",
    "tests/test_task038_gateway_blind_test.py",
)
# The thin adapters and contracts the live clients plug into keep passing unchanged.
AFFECTED = tuple(sorted(p.relative_to(ROOT).as_posix() for p in ROOT.glob("tests/imported/BIE_MODEL_GW_*/tests/model_gateway/test_*.py")))


def run_file(relative: str) -> dict:
    started = time.monotonic()
    name = "task038_" + relative.replace("/", "_").removesuffix(".py")
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    failed = [test.id().rsplit(".", 1)[-1] for test, _ in result.failures + result.errors]
    if result.failures or result.errors:
        print(stream.getvalue(), file=sys.stderr)
    return {"file": relative, "tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
            "skips": len(result.skipped), "failed_methods": failed, "seconds": round(time.monotonic() - started, 3)}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    rows = [run_file(path) for path in NEW + AFFECTED]
    totals = {key: sum(row[key] for row in rows) for key in ("tests", "failures", "errors", "skips")}
    passed = totals["failures"] == totals["errors"] == 0 and all(row["tests"] > 0 for row in rows) and len(AFFECTED) >= 25
    summary = {"lane": "task038", "passed": passed, **totals, "files": len(rows), "evidence_kind": "TECHNICAL_TEST",
               "product_accepted": False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"summary": summary, "results": rows}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
