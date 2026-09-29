"""Read-only unsigned audit. No keys in JSON, network fetches or rights inference.

Exit 0: bounded checks pass;3: review required;2: blockers;4: invalid input/output.
The default unsigned CLI cannot certify legal clearance or authorize publication.
"""
from pathlib import Path
import argparse,sys
from ..source_v2.codec import loads
from ..repair_v2.codec import decode
from ..repair_audit_v2.io import write_new
from ..release_v2.contracts import ContractError,canonical_bytes
from .models import RightsRequest,RightsPolicy
from .evaluator import evaluate

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--request',type=Path,required=True);p.add_argument('--policy',type=Path,required=True)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--as-of',type=int,required=True);p.add_argument('--output',type=Path)
    a=p.parse_args()
    try:
        if a.output and (a.output.resolve()==a.root.resolve() or a.output.resolve().is_relative_to(a.root.resolve())):raise ContractError('RIGHTS_OUTPUT_INSIDE_SNAPSHOT')
        for f in (a.request,a.policy):
            if f.is_symlink() or not f.is_file() or f.stat().st_size>4194304:raise ContractError('RIGHTS_CLI_INPUT')
        req=decode(loads(a.request.read_bytes()),RightsRequest);policy=decode(loads(a.policy.read_bytes()),RightsPolicy)
        r=evaluate(req,a.root,policy,as_of=a.as_of);b=canonical_bytes(r.to_dict())+b'\n'
        if a.output:write_new(a.output,b)
        else:sys.stdout.buffer.write(b)
        return {'CHECKS_PASSED':0,'REVIEW_REQUIRED':3,'BLOCKED':2}[r.status]
    except (ContractError,OSError,UnicodeError) as ex:
        print(ex.code if isinstance(ex,ContractError) else 'RIGHTS_CLI_IO',file=sys.stderr);return 4
if __name__=='__main__':raise SystemExit(main())
