"""Read-only local index verification. Pin the blueprint digest independently.

No key material or executable callback is accepted from these JSON documents.
Exit 0: verified metadata only; 2: invalid/unverified input. Never authorizes release.
"""
from pathlib import Path
import argparse,json,sys
from .index import load,verify_index
from ..release_v2.contracts import ContractError,digest

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--blueprint',default='metadata/section16/INDEX_BLUEPRINT.json')
    p.add_argument('--blueprint-sha256',required=True)
    p.add_argument('--index',default='metadata/section16/TASK_INTEGRATION_INDEX.json')
    p.add_argument('--receipt',default='hardening/section16_h2/evidence/final_source_suites/TEST_RESULT.json')
    a=p.parse_args(argv)
    try:
        bp=load(a.root,a.blueprint)
        if digest(bp)!=a.blueprint_sha256:raise ContractError('INDEX_BLUEPRINT_PIN_MISMATCH')
        # Registered, installed suite definitions; never import a path from request JSON.
        from .suite_catalog import LOCAL_SUITES
        result=verify_index(a.root,load(a.root,a.index),bp,receipt_path=a.receipt,suite_specs=LOCAL_SUITES)
        print(json.dumps(result,sort_keys=True));return 0
    except (ContractError,OSError,ValueError,KeyError,TypeError) as exc:
        print(json.dumps({'status':'BLOCKED','error':str(exc),'product_accepted':False},sort_keys=True));return 2
if __name__=='__main__':raise SystemExit(main())
