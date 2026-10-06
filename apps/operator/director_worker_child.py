"""Bounded trusted Task033 child. Technical providers require an explicit flag."""
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
    enforcement = enforce_current_process(PdfProcessBudget())
    from apps.operator.contracts import Credentials, Principal
    from apps.operator.service import Service
    from apps.operator.director_producer import DirectorProducerControlPlane
    from bie.productization.director_contract import PROFILE
    credentials = Credentials()
    principal = Principal("local-producer", args.tenant, frozenset({"read", "worker"}), time.time() + 60)
    credentials.grant(os.environ.get("BIE_OPERATOR_TOKEN", ""), principal)
    port = DirectorProducerControlPlane(Service(args.data_root, credentials), enabled_profiles={PROFILE})
    stack = None
    if args.technical_test_providers and not args.verify_only:
        sys.path.insert(0, str(ROOT / "tests/productization/director"))
        from protocol_support import make_stack
        stack = make_stack()
    result = port.status(principal, args.run_id)
    if not args.verify_only:
        for _ in range(8):
            result = port.work_once(principal, args.run_id, director_stack=stack)
            if result["slice_complete"] or any(s in ("FAILED", "BLOCKED") for s in result["stages"].values()):
                break
    # Compact the identical safe status object within the unchanged 4096-byte
    # parent supervision limit. Never widen the limit or omit artifact identity.
    print(json.dumps(dict(enforcement=enforcement, result=result), sort_keys=True,
                     separators=(",", ":")))
    blocked_math = result.get("safe_diagnostics") == {"MATH": ["math_review_required"]}
    return 0 if result["slice_complete"] or blocked_math else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        print('{"code":"director_worker_failed","product_accepted":false}')
        raise SystemExit(2) from None
