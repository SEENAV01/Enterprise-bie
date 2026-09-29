"""Read-only preview: TASK REQUEST POLICY --root ARTIFACT_ROOT. Exit3 is review."""
import argparse,json
from pathlib import Path
from ..release_v2.contracts import ContractError
from .service import preview,read_request,read_policy,WORKERS

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('task',choices=tuple(WORKERS));p.add_argument('request',type=Path);p.add_argument('policy',type=Path);p.add_argument('--root',required=True,type=Path)
    a=p.parse_args()
    try:
        if a.request.stat().st_size>16777216 or a.policy.stat().st_size>16777216:raise ContractError('MEDIA_REPAIR_CLI_INPUT_LIMIT')
        data,witness=preview(a.task,read_request(a.task,a.request.read_bytes()),a.root,read_policy(a.task,a.policy.read_bytes()))
        print(json.dumps(dict(status='UNAUTHORIZED_PREVIEW_ONLY',payload_utf8=data.decode('utf-8'),witness=witness,publication_performed=False,product_accepted=False),indent=2));return 3
    except (ContractError,OSError,ValueError,TypeError,KeyError) as exc:
        print(json.dumps(dict(status='ESCALATION_REQUIRED',reason=exc.code if isinstance(exc,ContractError) else type(exc).__name__,product_accepted=False)));return 2
if __name__=='__main__':raise SystemExit(main())
