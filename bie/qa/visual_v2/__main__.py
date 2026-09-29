"""Unsigned offline execution. Authentication keys are only supplied out of band."""
import argparse,json,sys
from pathlib import Path
from ..release_v2.contracts import ContractError,canonical_bytes
from .codec import load_request,load_policy,load_reviews
from .evaluator import evaluate

def bounded_read(path,limit=4*1024*1024):
    with path.open('rb') as f:data=f.read(limit+1)
    if len(data)>limit:raise ContractError('CLI_INPUT_SIZE_LIMIT')
    return data

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--request',required=True,type=Path);p.add_argument('--policy',required=True,type=Path)
    p.add_argument('--artifact-root',required=True,type=Path);p.add_argument('--as-of',required=True,type=int)
    p.add_argument('--reviews',type=Path);p.add_argument('--output',type=Path);args=p.parse_args(argv)
    try:
        r=load_request(bounded_read(args.request));policy=load_policy(bounded_read(args.policy))
        reviews=load_reviews(bounded_read(args.reviews)) if args.reviews else ()
        result=evaluate(r,args.artifact_root,policy,as_of=args.as_of,reviews=reviews)
        data=canonical_bytes(result.to_dict())+b'\n'
        if args.output:
            with args.output.open('xb') as f:f.write(data)
        else:sys.stdout.buffer.write(data)
        return {'CHECKS_PASSED':0,'BLOCKED':2,'REVIEW_REQUIRED':3}[result.status]
    except (ContractError,OSError) as exc:
        print(json.dumps(dict(error=exc.code if isinstance(exc,ContractError) else 'CLI_FILESYSTEM_ERROR',product_accepted=False)),file=sys.stderr);return 4
if __name__=='__main__':raise SystemExit(main())
