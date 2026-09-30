"""Explicit local native campaign operations. No publication, deployment or Git writes."""
import argparse
import json
from pathlib import Path
from ..models import strict_loads
from ..native_qa.__main__ import read_bounded
from .contracts import Plan
from .runtime import Campaign


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('operation', choices=('init', 'run', 'summary', 'cancel'))
    p.add_argument('--campaign-dir', required=True, type=Path)
    p.add_argument('--expected-plan-sha256', required=True)
    p.add_argument('--plan', type=Path)
    p.add_argument('--artifact-root', type=Path)
    p.add_argument('--owner', default='local-operator')
    p.add_argument('--job-id')
    a = p.parse_args(argv)
    try:
        if a.operation == 'init' and a.plan is None:
            raise ValueError('--plan is required for init')
        path = a.plan if a.operation == 'init' else a.campaign_dir/'PLAN.json'
        plan = Plan(strict_loads(read_bounded(path, 2_000_000)), a.expected_plan_sha256)
        campaign = Campaign.create(a.campaign_dir, plan) if a.operation == 'init' else Campaign(a.campaign_dir, plan)
        if a.operation == 'run':
            if a.artifact_root is None: raise ValueError('--artifact-root is required')
            output = campaign.run(a.artifact_root, a.owner)
        elif a.operation == 'cancel':
            if a.job_id is None: raise ValueError('--job-id is required')
            output = campaign.cancel(a.job_id)
        else:
            output = campaign.summary()
        output = dict(output, local_canonical_cli_route_executed=True, status='BLOCKED',
                      release_authorized=False, product_accepted=False)
    except Exception as exc:
        output = dict(status='BLOCKED', error_code=getattr(exc, 'code', 'CAMPAIGN_OPERATOR_ERROR'),
                      exception_type=type(exc).__name__, release_authorized=False, product_accepted=False)
    print(json.dumps(output, sort_keys=True))
    # Current three-metric unsigned benchmark remains blocked, including init,
    # summary and technical positives. A zero is never a disguised release PASS.
    return 2

if __name__ == '__main__': raise SystemExit(main())
