"""Read-only local transformation preview. No credentials, publication or acceptance.

python -m bie.qa.domain_repair_v2 TASK REQUEST POLICY --root ARTIFACT_ROOT
Only preview bytes/diffs are returned to stdout. Governed generation/prepare API
requires inventory plus generation approvals; staged execution needs a NEW approval.
"""
import argparse,json,sys
from dataclasses import asdict
from pathlib import Path
from ..release_v2.contracts import ContractError,canonical_bytes
from .common import read_request,read_policy
from .service import WORKERS
from .contracts import Limits

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('task',choices=tuple(WORKERS));p.add_argument('request',type=Path);p.add_argument('policy',type=Path);p.add_argument('--root',type=Path,required=True)
    a=p.parse_args()
    try:
        r=read_request(a.task,a.request.read_bytes());policy=read_policy(a.task,a.policy.read_bytes())
        after,witness=WORKERS[a.task](r,a.root,policy,Limits())
        print(json.dumps(dict(status='UNAUTHORIZED_PREVIEW_ONLY',request=asdict(after),witness=witness,
            publication_performed=False,product_accepted=False),indent=2));return 3
    except (ContractError,OSError,ValueError,TypeError,KeyError) as exc:
        print(json.dumps(dict(status='ESCALATION_REQUIRED',reason=exc.code if isinstance(exc,ContractError) else type(exc).__name__,product_accepted=False)));return 2
if __name__=='__main__':raise SystemExit(main())
