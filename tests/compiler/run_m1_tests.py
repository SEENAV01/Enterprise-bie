"""Unique supplemental M1/native inventory; original Task035 lanes stay separate."""
import argparse
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import platform
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
NEW = ("tests/compiler/test_producer_motion_m1.py", "tests/compiler/test_motion_m1_preservation.py",
       "tests/compiler/test_motion_m1_evidence.py")
SAFETY = ("tests/productization/animation/test_ci_r1_diagnostics.py",
          "tests/productization/animation/test_ci_r2_provisioning.py")


def inventory():
    spec = importlib.util.spec_from_file_location("m1_task035_inventory", ROOT / "tools/run_task035_tests.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    inherited = set(module.runner.NEW + module.runner.AFFECTED)
    extra = sorted({p.relative_to(ROOT).as_posix() for folder in ("tests/compiler", "tests/scene_ir")
                    for p in (ROOT / folder).glob("test*.py")} - inherited - set(NEW) - set(SAFETY))
    return {"new": list(NEW), "native-extra": extra, "safety": list(SAFETY)}, inherited


def cases(suite):
    for test in suite:
        if isinstance(test, unittest.TestSuite): yield from cases(test)
        else: yield test


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lane", choices=("new", "native-extra", "safety"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    selected, inherited = inventory()
    rows, identities = [], set()
    started = time.monotonic()
    for path in selected[args.lane]:
        # Keep source directory imports identical to the canonical file runner.
        sys.path.insert(0, str((ROOT / path).parent))
        row = {"file": path, "selected": 0, "executed": 0, "failures": 0, "errors": 0, "skips": 0}
        capture = io.StringIO()
        try:
            with redirect_stdout(capture), redirect_stderr(capture):
                name = "m1_" + hashlib.sha256(path.encode()).hexdigest()[:16]
                spec = importlib.util.spec_from_file_location(name, ROOT / path)
                module = importlib.util.module_from_spec(spec); sys.modules[name] = module
                spec.loader.exec_module(module)
                suite = module.selected_suite() if hasattr(module, "selected_suite") else unittest.defaultTestLoader.loadTestsFromModule(module)
                local = [path + "::" + t.id().split(".", 1)[1] for t in cases(suite)]
                if len(local) != len(set(local)) or identities.intersection(local):
                    raise ValueError("M1_DUPLICATE_TEST_IDENTITY")
                identities.update(local); row["selected"] = len(local)
                result = unittest.TextTestRunner(stream=capture).run(suite)
                row.update(executed=result.testsRun, failures=len(result.failures), errors=len(result.errors),
                    skips=len(result.skipped), failed_methods=[t.id().split(".")[-1] for t,_ in result.failures+result.errors])
        except Exception as exc:
            row.update(errors=row["errors"]+1, collector_error=type(exc).__name__)
        row["passed"] = row["selected"] > 0 and row["executed"] == row["selected"] and not any(row[k] for k in ("failures","errors","skips"))
        rows.append(row); print(json.dumps(row, sort_keys=True), flush=True)
        capture.close()
    summary = {k: sum(r[k] for r in rows) for k in ("selected","executed","failures","errors","skips")}
    summary.update(passed=bool(rows) and all(r["passed"] for r in rows), platform=platform.system(),
        lane=args.lane, source_files=len(rows), unique_identity_sha256=hashlib.sha256("\n".join(sorted(identities)).encode()).hexdigest(),
        elapsed_s=round(time.monotonic()-started,3), diagnostic_repeats_counted=False, product_accepted=False)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps({"summary":summary,"results":rows},indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,sort_keys=True)); return 0 if summary["passed"] else 1


if __name__ == "__main__": raise SystemExit(main())
