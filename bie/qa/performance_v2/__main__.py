"""Read-only performance audit. Never executes producer commands from a request."""
import argparse
from pathlib import Path
from .codec import decode,loads
from .models import PerformanceRequest,PerformancePolicy
from .evaluator import evaluate
from ..release_v2.contracts import ContractError,canonical_bytes
from ..repair_audit_v2.io import write_new

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('request',type=Path);p.add_argument('policy',type=Path);p.add_argument('--root',type=Path,required=True);p.add_argument('--as-of',type=int,required=True);p.add_argument('--output',type=Path)
    a=p.parse_args()
    try:
        r=decode(loads(a.request.read_bytes()),PerformanceRequest);policy=decode(loads(a.policy.read_bytes()),PerformancePolicy)
        result=evaluate(r,a.root,policy,as_of=a.as_of);data=canonical_bytes(result.to_dict())
        if a.output:write_new(a.output,data)
        print(data.decode());return {'CHECKS_PASSED':0,'REVIEW_REQUIRED':3,'BLOCKED':2}[result.status]
    except (ContractError,OSError,ValueError) as e:
        print(canonical_bytes({'status':'BLOCKED','code':e.code if isinstance(e,ContractError) else 'PERF_IO','product_accepted':False}).decode());return 4
if __name__=='__main__':raise SystemExit(main())
