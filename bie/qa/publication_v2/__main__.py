"""Read-only release inspection; this CLI cannot sign, revoke or deploy a release."""
from pathlib import Path
import argparse,json,sys
from .codec import loads
from .contracts import PublicationPolicy,MAX_METADATA
from .evaluator import assess
from ..release_v2.contracts import ContractError

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('request',type=Path);p.add_argument('--root',type=Path,required=True)
    p.add_argument('--environment',required=True);p.add_argument('--as-of',type=int,required=True)
    a=p.parse_args()
    try:
        with a.request.open('rb') as f:req=loads(f.read(MAX_METADATA+1))
        report=assess(req,a.root,PublicationPolicy(a.environment),as_of=a.as_of)
        print(report.to_bytes().decode());return 0 if report.ready_for_signing else 3
    except (ContractError,OSError) as e:
        print(json.dumps(dict(status='BLOCKED',code=e.code if isinstance(e,ContractError) else 'IO_ERROR',release_authorized=False,product_accepted=False)))
        return 4
if __name__=='__main__':raise SystemExit(main())
