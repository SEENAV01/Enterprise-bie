"""Explicit operator entrypoint for canonical BenchmarkAPI; no network listener."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from ..models import strict_loads
from ..native_qa.__main__ import read_bounded
from ..native_campaign import Campaign, Plan
from .admission import Admission, context
from .service import Service


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=('init-admission','cases','run','summary','reconcile'))
    parser.add_argument('--campaign-dir',type=Path,required=True)
    parser.add_argument('--expected-plan-sha256',required=True)
    parser.add_argument('--registry',type=Path,required=True)
    parser.add_argument('--scope-id',required=True)
    parser.add_argument('--artifact-root',type=Path,required=True)
    parser.add_argument('--owner',default='local-api-operator')
    parser.add_argument('--case-id')
    parser.add_argument('--artifact-refs',type=Path)
    parser.add_argument('--domain')
    args = parser.parse_args(argv)
    try:
        plan = Plan(strict_loads(read_bounded(args.campaign_dir/'PLAN.json',2_000_000)),args.expected_plan_sha256)
        campaign = Campaign(args.campaign_dir,plan)
        data = plan.data()
        cfg = context(args.scope_id,data['runtime_sha256'],data['policy_sha256'])
        admission = (Admission.create(args.registry,cfg) if args.operation == 'init-admission'
                     else Admission(args.registry,cfg))
        service = Service(campaign,args.artifact_root,admission,args.owner)
        if args.operation == 'run':
            if args.case_id is None or args.artifact_refs is None:
                raise ValueError('run requires --case-id and --artifact-refs')
            result = service.run(args.case_id,strict_loads(read_bounded(args.artifact_refs,2_000_000)))
        elif args.operation == 'cases':
            result = dict(cases=list(service.cases(args.domain)))
        elif args.operation == 'reconcile':
            if args.case_id is None:
                raise ValueError('reconcile requires --case-id')
            result = service.runner.reconcile(args.case_id)
        else:
            result = service.summary()
        output = dict(result,status='BLOCKED',release_authorized=False,product_accepted=False)
    except Exception as exc:
        output = dict(status='BLOCKED',error_code=getattr(exc,'code','API_OPERATOR_ERROR'),
                      exception_type=type(exc).__name__,release_authorized=False,product_accepted=False)
    print(json.dumps(output,sort_keys=True))
    # This development AV subset cannot authorize a benchmark release.
    return 2

if __name__ == '__main__':
    raise SystemExit(main())
