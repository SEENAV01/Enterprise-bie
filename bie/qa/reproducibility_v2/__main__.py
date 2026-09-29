"""Read-only audit of stored reproduction evidence. No executable imports from JSON."""
import argparse,sys
from pathlib import Path
from ..release_v2.contracts import ContractError,canonical_bytes
from ..source_v2.codec import loads
from ..repair_v2.codec import decode
from ..repair_audit_v2.io import write_new
from .models import ReproRequest,ReproPolicy
from .evaluator import evaluate

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('request','policy','source-root','evidence-root','output'):p.add_argument('--'+n,required=True,type=Path)
    p.add_argument('--as-of',required=True,type=int);a=p.parse_args()
    try:
        if any(a.output.resolve().is_relative_to(r.resolve()) for r in (a.source_root,a.evidence_root)) or a.output.resolve() in {a.request.resolve(),a.policy.resolve()}:raise ContractError('REPRO_CLI_OUTPUT_OVERLAP')
        for f in (a.request,a.policy):
            if f.is_symlink() or not f.is_file() or f.stat().st_size>4194304:raise ContractError('REPRO_CLI_INPUT')
        request=decode(loads(a.request.read_bytes()),ReproRequest);policy=decode(loads(a.policy.read_bytes()),ReproPolicy)
        result=evaluate(request,a.source_root,a.evidence_root,policy,as_of=a.as_of)
        write_new(a.output,canonical_bytes(result.to_dict()));print(result.status)
        return 2 if result.status=='BLOCKED' else 3 if result.status=='REVIEW_REQUIRED' else 0
    except (ContractError,OSError) as ex:
        print(ex.code if isinstance(ex,ContractError) else 'REPRO_CLI_IO',file=sys.stderr);return 4
if __name__=='__main__':raise SystemExit(main())
