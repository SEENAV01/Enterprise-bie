"""Task030 trusted bounded child; credentials stay in process environment only."""
import argparse
import json
import os
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from apps.operator.process_limits import PdfProcessBudget,enforce_current_process


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--data-root",type=Path,required=True)
    parser.add_argument("--run-id",required=True);parser.add_argument("--tenant",required=True)
    parser.add_argument("--verify-only",action="store_true")
    args=parser.parse_args();enforcement=enforce_current_process(PdfProcessBudget())
    from apps.operator.contracts import Credentials,Principal
    from apps.operator.service import Service
    from apps.operator.reasoning_producer import ReasoningProducerControlPlane
    from bie.productization.pr_reasoning import PROFILE
    credentials=Credentials()
    principal=Principal("local-producer",args.tenant,frozenset({"read","worker"}),time.time()+60)
    credentials.grant(os.environ.get("BIE_OPERATOR_TOKEN",""),principal)
    port=ReasoningProducerControlPlane(Service(args.data_root,credentials),enabled_profiles={PROFILE})
    result=port.status(principal,args.run_id)
    if not args.verify_only:
        for _ in range(5):
            result=port.work_once(principal,args.run_id)
            if result["slice_complete"] or any(v in ("FAILED","BLOCKED") for v in result["stages"].values()):break
    print(json.dumps(dict(enforcement=enforcement,result=result),sort_keys=True))
    # BLOCKED is governed evidence, not producer success; parent checks exact state.
    return 0 if result["slice_complete"] or result["safe_diagnostics"]=={"REASONING":["math_evidence_required"]} else 2


if __name__=="__main__":
    try:raise SystemExit(main())
    except Exception:
        print('{"code":"producer_worker_failed","product_accepted":false}')
        raise SystemExit(2) from None
