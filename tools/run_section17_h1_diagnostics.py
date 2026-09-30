#!/usr/bin/env python3
"""Persist controlled H1 gate scenarios; no real production run or reviews occur.

Test-only signing identities and invented evidence exercise validation mechanics.
A synthetic gate PASS must never be reported as a real benchmark/native PASS.
"""
from __future__ import annotations
import argparse, json, sys, time
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests/section17'));sys.dont_write_bytecode=True
from h1_helpers import gate_fixture_args
from bie.evaluation.benchmarks.models import BenchmarkError,digest
from bie.evaluation.benchmarks.release.ledger import ReleaseLedger
from bie.evaluation.benchmarks.release.supervised import SupervisedProvider
from bie.evaluation.benchmarks.release import gate

def dump(path,body):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(body,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

class HangingFixture:
    provider_id='h1-fixture';model_version='v1';fixture_only=True
    def complete(self,request):
        time.sleep(30)
        return '{}'

def hanging_factory():return HangingFixture()

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',required=True)
    args=parser.parse_args();out=Path(args.output_dir);out.mkdir(parents=True,exist_ok=False)
    scenarios=[]
    def scenario(name,change,expected):
        a=gate_fixture_args();change(a)
        a['expected_manifest_sha256']=digest(a['manifest']);a['expected_policy_sha256']=digest(a['policy'])
        scenarios.append((name,a,expected))
    scenario('synthetic_contract_positive',lambda a:None,'PASS')
    scenario('candidate_bundle_absent',lambda a:a.pop('candidate_bundle'),'BLOCKED')
    scenario('assessment_authorizations_absent',lambda a:a.pop('assessment_tokens'),'BLOCKED')
    scenario('coverage_contract_absent',lambda a:a.pop('coverage_contract'),'BLOCKED')
    scenario('candidate_bytes_changed',lambda a:a['candidate_bundle']['candidates'].__setitem__('math-1',{'changed':True}),'BLOCKED')
    scenario('reviewer_revoked',lambda a:a['trust']['human'].__setitem__('revoked',True),'BLOCKED')
    scenario('artifact_manifest_substitution',lambda a:a['manifest'].__setitem__('artifact_sha256',digest('other-artifact')),'BLOCKED')
    scenario('required_coverage_increased',lambda a:a['coverage_contract']['domains'][0]['metrics'][0].__setitem__('minimum_groups',2),'BLOCKED')
    results=[]
    with ReleaseLedger(out/'release.sqlite3') as db:
        for name,a,expected in scenarios:
            receipt=db.execute(campaign_id=name,attempt_id=name,**a)
            report=receipt['report']
            assert report['release_authorized'] is False and report['product_accepted'] is False
            dump(out/f'results/{name}.json',receipt)
            results.append({'id':name,'expected':expected,'actual':report['outcome'],
                'matched':report['outcome']==expected,'reasons':report['reasons'],
                'synthetic_inputs':True,'real_production_approval':False})
        try:
            with patch.object(gate,'evaluate',side_effect=KeyboardInterrupt):
                db.execute(campaign_id='interrupted',attempt_id='interrupted',**gate_fixture_args())
        except KeyboardInterrupt:pass
        row=db.db.execute("SELECT inputs_sha,state FROM release_attempts WHERE id='interrupted'").fetchone()
        assert row[1]=='RUNNING'
        recovered=db.recover_incomplete('interrupted',expected_inputs_sha256=row[0],operator_id='test-operator',reason='fixture-interruption')
        dump(out/'results/interruption_recovered.json',recovered)
    with ReleaseLedger(out/'release.sqlite3') as db:
        persisted=all(db.get(r['id'])['report']['outcome']==r['actual'] for r in results)
        recovery_persisted=db.get('interrupted')==recovered
    worker=SupervisedProvider(hanging_factory,provider_id='h1-fixture',model_version='v1',fixture_only=True,timeout_seconds=.2)
    reason=None
    try:worker.complete({'fixture':'deadline-control'})
    except BenchmarkError as exc:reason=exc.code
    deadline_ok=reason=='MODEL_PROVIDER_DEADLINE_EXCEEDED' and worker.last_observation['worker_reaped']
    summary={'scope':'SYNTHETIC_H1_TRUST_AND_DURABILITY_CONTROLS_NOT_NATIVE_ACCEPTANCE',
        'scenario_count':len(results),'scenarios':results,'all_expected_outcomes_matched':all(r['matched'] for r in results),
        'persisted_after_reopen':persisted,'recovered_reservation_persisted':recovery_persisted,
        'worker_deadline_control':{'reason':reason,'observation':worker.last_observation,'matched':deadline_ok},
        'live_model_calls':0,'real_human_reviews':0,'native_bie_runs':0,'real_production_approvals':0,
        'section_complete':False,'product_accepted':False,'release_authorized':False}
    dump(out/'DIAGNOSTIC_RESULT.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k!='scenarios'},indent=2))
    return 0 if all([summary['all_expected_outcomes_matched'],persisted,recovery_persisted,deadline_ok]) else 1
if __name__=='__main__':raise SystemExit(main())
