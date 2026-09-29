"""Read-only unsigned audit CLI. Trust provisioning stays in the operator API."""
from pathlib import Path
import argparse,sys
from ..release_v2.contracts import ContractError,canonical_bytes
from ..repair_v2.codec import load_policy as repair_policy
from .codec import load_request,load_policy
from .evaluator import evaluate
from .io import write_new

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('request',type=Path);p.add_argument('repair_policy',type=Path);p.add_argument('audit_policy',type=Path)
    p.add_argument('--original-root',type=Path,required=True);p.add_argument('--candidate-root',type=Path,required=True)
    p.add_argument('--as-of',type=int,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    try:
        for root in (args.original_root,args.candidate_root):
            if args.output.resolve().is_relative_to(root.resolve()):raise ContractError('AUDIT_OUTPUT_INSIDE_INPUT')
        for path in (args.request,args.repair_policy,args.audit_policy):
            if path.is_symlink() or not path.is_file() or path.stat().st_size>4194304:raise ContractError('AUDIT_CLI_INPUT')
        result=evaluate(load_request(args.request.read_bytes()),args.original_root,args.candidate_root,
            repair_policy(args.repair_policy.read_bytes()),load_policy(args.audit_policy.read_bytes()),as_of=args.as_of)
        write_new(args.output,canonical_bytes(result.to_dict())+b'\n')
        print(result.status)
        return 2 if result.status=='BLOCKED' else 3 if result.status=='REVIEW_REQUIRED' else 0
    except (ContractError,OSError,ValueError) as exc:
        print(exc.code if isinstance(exc,ContractError) else 'AUDIT_CLI_INVALID',file=sys.stderr);return 4
if __name__=='__main__':raise SystemExit(main())
