"""Baseline-qualified seeded fault controls; never new distinct test counts.

All effects are process-local against disposable synthetic test stores. Do not
disable the real OS memory limit and then attempt a large host allocation.
"""
from pathlib import Path
import argparse
import io
import json
import os
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests/section18'))
from test_batchh1c import ProcessBounds,CancelRecovery,WorkerProcessBoundary
import test_batchh1c as target_tests
from apps.operator.service import Service
from apps.operator.process_limits import PdfProcessBudget
from apps.operator.process_supervision import ChildOutcome
import apps.operator.pdf_validation as parser
import apps.operator.worker_execution as worker


def run(cls,method):
    stream=io.StringIO()
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.TestSuite([cls(method)]))
    return dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),
                skips=len(result.skipped),passed=result.wasSuccessful() and not result.skipped)


def main():
    args=argparse.ArgumentParser();args.add_argument('receipt',type=Path);a=args.parse_args()
    original_environment=parser.child_environment
    def unsafe_environment():
        return dict(original_environment(),OPENAI_API_KEY=os.environ.get('OPENAI_API_KEY',''))
    original_control=Service.control
    def foreign_control(service,p,*args):
        if p.tenant=='other-tenant':
            p=next(v for v in service.credentials._grants.values() if v.tenant=='tenant-a')
        return original_control(service,p,*args)
    valid=dict(enforcement='LINUX_RLIMIT',result=dict(outcome='TERMINAL',dispatched=False))
    controls=[
        ('FALSE_VALID',ProcessBounds,'test_invalid_pdf_is_invalid_not_fake_valid',
         lambda:patch.object(target_tests,'inspect_source',return_value=dict(status='VALID'))),
        ('CREDENTIAL_PROPAGATION',ProcessBounds,'test_no_provider_credentials_in_child_environment',
         lambda:patch.object(parser,'child_environment',side_effect=unsafe_environment)),
        ('WIDEN_BUDGET',ProcessBounds,'test_invalid_process_limits_reject_booleans_and_widening',
         lambda:patch.object(PdfProcessBudget,'__post_init__',lambda self:None)),
        ('IGNORE_PENDING_INTENT',CancelRecovery,'test_pending_cancel_read_never_claims_cancelled',
         lambda:patch.object(Service,'_no_pending_control',lambda *args:None)),
        ('FOREIGN_CANCEL',CancelRecovery,'test_foreign_tenant_cannot_reconcile',
         lambda:patch.object(Service,'control',side_effect=foreign_control,autospec=True)),
        ('WORKER_CONTRACT_SUBSTITUTION',WorkerProcessBoundary,'test_worker_child_contract_does_not_echo_internal_detail',
         lambda:patch.object(worker,'strict_json',return_value=valid)),
    ]
    rows=[]
    for name,cls,method,mutate in controls:
        baseline=run(cls,method)
        if baseline['passed']:
            with mutate():fault=run(cls,method)
        else:fault=None
        rows.append(dict(name=name,target=cls.__name__+'.'+method,baseline=baseline,fault=fault,
                         killed=bool(fault and fault['failures']>0 and fault['errors']==fault['skips']==0),
                         harness_error=bool(fault and (fault['errors'] or fault['skips']))))
    receipt=dict(schema='bie.section18.h1-003.qualified-controls/1',controls=rows,
                 passed=all(r['baseline']['passed'] and r['killed'] and not r['harness_error'] for r in rows),
                 additional_distinct_test_count=0,unsafe_memory_fault_disabled=False,
                 fixture_only=True,real_book_acceptance=False,product_accepted=False)
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,sort_keys=True))
    return 0 if receipt['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
