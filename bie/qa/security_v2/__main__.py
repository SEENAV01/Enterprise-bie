"""Read-only unsigned audit. No request-supplied callbacks or sandbox weakening.

Exit 3 review required;2 blocked;4 invalid input/output. Does not execute candidate code.
Parser paths are separate operator options; hashes must match the supplied policy.
"""
from pathlib import Path
import argparse,sys
from ..source_v2.codec import loads
from .codec import decode
from ..repair_audit_v2.io import write_new
from ..release_v2.contracts import ContractError,canonical_bytes
from .models import SecurityRequest,SecurityPolicy
from .scanner import Toolchain
from .evaluator import evaluate

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('request','policy','root'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--as-of',type=int,required=True);p.add_argument('--output',type=Path);p.add_argument('--node',type=Path);p.add_argument('--typescript',type=Path)
    a=p.parse_args()
    try:
        if a.output and a.output.resolve().is_relative_to(a.root.resolve()):raise ContractError('SEC_OUTPUT_INSIDE_SNAPSHOT')
        for f in (a.request,a.policy):
            if f.is_symlink() or not f.is_file() or f.stat().st_size>4194304:raise ContractError('SEC_CLI_INPUT')
        request=decode(loads(a.request.read_bytes()),SecurityRequest);policy=decode(loads(a.policy.read_bytes()),SecurityPolicy)
        if bool(a.node)!=bool(a.typescript):raise ContractError('SEC_CLI_PARSER_PAIR')
        tools=Toolchain(str(a.node),policy.parser_node_sha256,str(a.typescript),policy.parser_typescript_sha256) if a.node else None
        result=evaluate(request,a.root,policy,as_of=a.as_of,toolchain=tools);b=canonical_bytes(result.to_dict())+b'\n'
        if a.output:write_new(a.output,b)
        else:sys.stdout.buffer.write(b)
        return {'CHECKS_PASSED':0,'REVIEW_REQUIRED':3,'BLOCKED':2}[result.status]
    except (ContractError,OSError,UnicodeError) as e:
        print(e.code if isinstance(e,ContractError) else 'SEC_CLI_IO',file=sys.stderr);return 4
if __name__=='__main__':raise SystemExit(main())
