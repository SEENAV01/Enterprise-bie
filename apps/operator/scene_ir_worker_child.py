"""Real Task036 child; existing supervisor/resource contract, no rendering."""
import argparse
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--tenant", required=True)
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--technical-test-providers", action="store_true")
    args = parser.parse_args()
    from apps.operator.process_limits import PdfProcessBudget, enforce_current_process
    from apps.operator.contracts import Credentials, Principal
    from apps.operator.service import Service
    from apps.operator.scene_ir_producer import SceneIRProducerControlPlane
    from bie.productization.scene_ir_contract import PROFILE
    from bie.productization.contracts import digest
    enforcement = enforce_current_process(PdfProcessBudget())
    credentials = Credentials()
    principal = Principal("local-producer", args.tenant, frozenset({"read", "worker"}), time.time() + 60)
    credentials.grant(os.environ.get("BIE_OPERATOR_TOKEN", ""), principal)
    port = SceneIRProducerControlPlane(Service(args.data_root, credentials), enabled_profiles={PROFILE})
    stack = None
    if args.technical_test_providers and not args.verify_only:
        sys.path.insert(0, str(ROOT / "tests/productization/director"))
        from protocol_support import make_stack
        stack = make_stack()
    result = port.status(principal, args.run_id)
    if not args.verify_only:
        for _ in range(11):
            result = port.work_once(principal, args.run_id, director_stack=stack)
            if result["slice_complete"] or any(s in ("FAILED", "BLOCKED") for s in result["stages"].values()):
                break
    print(json.dumps(dict(enforcement=enforcement, run_id=args.run_id, status_sha256=digest(result),
        stages=result["stages"], scene_ir=result.get("scene_ir"), product_accepted=False),
        sort_keys=True, separators=(",", ":")))
    return 0 if result["slice_complete"] or result.get("safe_diagnostics") == {"MATH": ["math_review_required"]} else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        print('{"code":"scene_ir_worker_failed","product_accepted":false}')
        raise SystemExit(2) from None
