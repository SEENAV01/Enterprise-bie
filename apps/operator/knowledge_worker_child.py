"""Trusted bounded local Task029 child; no live credentials or HTTP admission."""
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
    parser.add_argument("--run-id",required=True)
    parser.add_argument("--tenant",required=True)
    args=parser.parse_args()
    enforcement=enforce_current_process(PdfProcessBudget())
    from apps.operator.contracts import Credentials,Principal
    from apps.operator.service import Service
    from apps.operator.knowledge_producer import KnowledgeProducerControlPlane
    from bie.productization.contracts import PROFILE
    credentials=Credentials()
    principal=Principal("local-producer",args.tenant,frozenset({"read","worker"}),time.time()+60)
    credentials.grant(os.environ.get("BIE_OPERATOR_TOKEN",""),principal)
    port=KnowledgeProducerControlPlane(Service(args.data_root,credentials),enabled_profiles={PROFILE})
    result=None
    for _ in range(3):
        result=port.work_once(principal,args.run_id)
        if result["slice_complete"] or any(v in ("FAILED","BLOCKED") for v in result["stages"].values()):break
    print(json.dumps(dict(enforcement=enforcement,result=result),sort_keys=True))
    return 0 if result["slice_complete"] else 2


if __name__=="__main__":
    try:raise SystemExit(main())
    except Exception:
        print('{"code":"producer_worker_failed","product_accepted":false}')
        raise SystemExit(2) from None
