"""Package-aware Task036-only inventory; inherited gates retain their owners."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests.compiler.run_m1_tests import run_file
from tests.productization.scene_ir.recovery_observations import capture_observations

NEW = (
    "tests/productization/scene_ir/test_scene_ir_admission.py",
    "tests/productization/scene_ir/test_scene_ir_contract.py",
    "tests/productization/scene_ir/test_scene_ir_producer.py",
    "tests/productization/scene_ir/test_scene_ir_conservation.py",
    "tests/productization/scene_ir/test_scene_ir_currentness.py",
    "tests/productization/scene_ir/test_scene_ir_recovery.py",
    "tests/productization/scene_ir/test_recovery_observations.py",
    "tests/productization/scene_ir/test_status_composition.py",
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    identities, rows = set(), []
    for path in NEW:
        # Only the actual child/recovery suite exports process observations.
        # Synthetic helper controls are a different evidence class, not workers.
        if path == 'tests/productization/scene_ir/test_scene_ir_recovery.py':
            with capture_observations() as observations:
                row = run_file(path, identities, ROOT)
            if observations:
                row['recovery_process_observations'] = observations
        else:
            row = run_file(path, identities, ROOT)
        rows.append(row)
        # Only runner-allowlisted identities/counts/codes, never unittest stderr.
        print(json.dumps(row, sort_keys=True), flush=True)
    summary = {k: sum(r[k] for r in rows) for k in ("selected", "executed", "failures", "errors", "skips", "collection_errors")}
    summary.update(passed=bool(rows) and all(r["passed"] for r in rows), platform=platform.system(),
        lane="task036-new", source_files=len(rows), unique_identity_sha256=hashlib.sha256(
            "\n".join(sorted(identities)).encode()).hexdigest(), elapsed_s=round(time.monotonic()-started, 3),
        diagnostic_repeats_counted=False, product_accepted=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(dict(summary=summary, results=rows), indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
