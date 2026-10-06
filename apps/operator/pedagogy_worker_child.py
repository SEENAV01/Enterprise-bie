"""Task032 trusted child under the unchanged local process and auth budgets."""
import argparse
import json
import os
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from apps.operator.process_limits import PdfProcessBudget, enforce_current_process


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--tenant", required=True)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    enforcement = enforce_current_process(PdfProcessBudget())
    from apps.operator.contracts import Credentials, Principal
    from apps.operator.service import Service
    from apps.operator.pedagogy_producer import PedagogyProducerControlPlane
    from bie.productization.pedagogy_plan import PROFILE

    credentials = Credentials()
    principal = Principal("local-producer", args.tenant,
                          frozenset({"read", "worker"}), time.time() + 60)
    credentials.grant(os.environ.get("BIE_OPERATOR_TOKEN", ""), principal)
    port = PedagogyProducerControlPlane(Service(args.data_root, credentials),
                                       enabled_profiles={PROFILE})
    result = port.status(principal, args.run_id)
    if not args.verify_only:
        for _ in range(7):
            result = port.work_once(principal, args.run_id)
            if result["slice_complete"] or any(
                    state in ("FAILED", "BLOCKED") for state in result["stages"].values()):
                break
    print(json.dumps(dict(enforcement=enforcement, result=result), sort_keys=True))
    blocked_math = result.get("safe_diagnostics") == {"MATH": ["math_review_required"]}
    return 0 if result["slice_complete"] or blocked_math else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        print('{"code":"producer_worker_failed","product_accepted":false}')
        raise SystemExit(2) from None
