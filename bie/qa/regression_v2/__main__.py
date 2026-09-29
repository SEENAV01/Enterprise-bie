"""Read-only unsigned comparison CLI. Policy is explicitly operator-provided.

Execution callbacks cannot be loaded from JSON. Use collect() with a registered
Python mapping to create execution evidence. This CLI only audits stored bytes.
"""
import argparse,sys
from pathlib import Path
from ..release_v2.contracts import ContractError,canonical_bytes
from ..source_v2.codec import loads
from ..repair_v2.codec import decode
from ..repair_audit_v2.io import write_new
from .models import RegressionRequest,RegressionPolicy
from .evaluator import evaluate

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('request','policy','baseline-root','candidate-root','evidence-root','output'):p.add_argument('--'+n,required=True,type=Path)
    p.add_argument('--as-of',type=int,required=True);a=p.parse_args()
    try:
        # CLI output must not be in either snapshot/evidence tree.
        if any(a.output.resolve().is_relative_to(r.resolve()) for r in (a.baseline_root,a.candidate_root,a.evidence_root)):
            raise ContractError('REG_OUTPUT_INPUT_OVERLAP')
        for f in (a.request,a.policy):
            if f.is_symlink() or not f.is_file() or f.stat().st_size>4194304:raise ContractError('REG_CLI_INPUT')
        request=decode(loads(a.request.read_bytes()),RegressionRequest);policy=decode(loads(a.policy.read_bytes()),RegressionPolicy)
        result=evaluate(request,a.baseline_root,a.candidate_root,a.evidence_root,policy,as_of=a.as_of)
        write_new(a.output,canonical_bytes(result.to_dict()))
        print(result.status)
        return 2 if result.status=='BLOCKED' else 3 if result.status=='REVIEW_REQUIRED' else 0
    except (ContractError,OSError) as e:
        print(e.code if isinstance(e,ContractError) else 'REG_IO_ERROR',file=sys.stderr);return 4
if __name__=='__main__':raise SystemExit(main())
