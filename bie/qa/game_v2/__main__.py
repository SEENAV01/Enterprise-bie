"""Read-only CLI. 0 checks passed; 2 blocked; 3 review; 4 invalid input/output."""
import argparse,json,sys
from pathlib import Path
from ..release_v2.contracts import ContractError
from .codec import load_request,load_policy
from .evaluator import evaluate

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--request',type=Path,required=True);p.add_argument('--policy',type=Path,required=True);p.add_argument('--artifact-root',type=Path,required=True);p.add_argument('--as-of',type=int,required=True);p.add_argument('--output',type=Path)
    a=p.parse_args()
    try:
        if a.output and a.output.exists():raise ContractError('GAME_OUTPUT_EXISTS')
        # Local operator request/policy are bounded before reading. No trust keys in JSON.
        if a.request.stat().st_size>4194304 or a.policy.stat().st_size>4194304:raise ContractError('GAME_INPUT_SIZE')
        r=evaluate(load_request(a.request.read_bytes()),a.artifact_root,load_policy(a.policy.read_bytes()),as_of=a.as_of)
        text=json.dumps(r.to_dict(),indent=2)+'\n'
        if a.output:
            with a.output.open('x',encoding='utf-8') as f:f.write(text)
        else:print(text,end='')
        return {'CHECKS_PASSED':0,'BLOCKED':2,'REVIEW_REQUIRED':3}[r.status]
    except (ContractError,OSError,ValueError) as e:
        print(json.dumps(dict(status='INVALID_INPUT',error=getattr(e,'code',type(e).__name__),product_accepted=False)),file=sys.stderr);return 4
if __name__=='__main__':raise SystemExit(main())
