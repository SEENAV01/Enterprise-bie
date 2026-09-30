"""Canonical API dispatch, real native AV results and bounded admission controls.

Unit orchestration mocks are explicitly separated from actual AV integration.
"""
from copy import deepcopy
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from native_campaign_support import request
from bie.evaluation.benchmarks.models import BenchmarkError, canonical_json, digest
from bie.evaluation.benchmarks.native_campaign import Plan, Campaign
from bie.evaluation.benchmarks.native_api import Admission, Service, context
from bie.evaluation.benchmarks.native_api.service import PlanRegistry, verify_native_api

ROOT = Path(__file__).resolve().parents[2]


class Setup(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='bie-native-api-test-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.assets = self.root/'assets'
        self.value = request(self.assets)
        self.plan = Plan(self.value,digest(self.value))
        self.campaign = Campaign.create(self.root/'campaign',self.plan)
        self.configuration = context('operator-development',self.value['runtime_sha256'],self.value['policy_sha256'])
        self.admission = Admission.create(self.root/'admission.sqlite',self.configuration)
        self.service = Service(self.campaign,self.assets,self.admission)
        self.job = self.value['jobs'][0]['job_id']
        self.refs = self.value['jobs'][0]['candidate_bundle']['candidate']['artifacts']

    def fake(self):
        # Unit-only orchestration payload, not a captured native evaluation.
        return dict(release_authorized=False,product_accepted=False,
                    native_qa_report={'release_status':'BLOCKED'},
                    native_component_consumer_executed=False,measurement_outcomes={'fixture':'PASS'})

    def unit_finished(self):
        with patch('bie.evaluation.benchmarks.native_campaign.runtime.bridge.execute',return_value=self.fake()):
            return self.service.run(self.job,self.refs)


class APIContracts(Setup):
    def test_actual_canonical_class_pin(self):
        from bie.infrastructure.benchmark_api import BenchmarkAPI
        self.assertIs(verify_native_api(),BenchmarkAPI)
        self.assertIs(type(self.service.native),BenchmarkAPI)

    def test_catalog_is_fixed_roster_and_detached(self):
        rows=self.service.cases();self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['domain'],'AV_TECHNICAL')
        rows[0]['expected_artifact_refs'].clear()
        self.assertEqual(len(self.service.cases()[0]['expected_artifact_refs']),len(self.refs))
        self.assertEqual(self.service.cases('nonexistent'),())
        self.assertEqual(self.service.cases('AV_TECHNICAL'),self.service.cases())

    def test_unknown_case_rejected_by_canonical_api(self):
        from bie.infrastructure.benchmark_api import BenchmarkAPIError
        with self.assertRaisesRegex(BenchmarkAPIError,'case not found'):
            self.service.run('unknown',self.refs)
        self.assertEqual(self.admission.snapshot()['attempts'],[])

    def test_unbounded_or_nonsequence_refs_rejected(self):
        for refs in (None,{},iter(self.refs),'bad',[],self.refs*2000):
            with self.subTest(kind=type(refs).__name__):
                with self.assertRaisesRegex(BenchmarkError,'TYPE_OR_COUNT'):
                    self.service.run(self.job,refs)
        self.assertEqual(self.admission.snapshot()['attempts'],[])

    def test_missing_extra_or_duplicate_ref_rejected_before_claim(self):
        bad=[self.refs[:-1],self.refs+self.refs[:1],self.refs+[dict(self.refs[0],artifact_id='extra')]]
        for refs in bad:
            with self.subTest(refs=len(refs)):
                with self.assertRaises(BenchmarkError):self.service.run(self.job,refs)
        self.assertEqual(self.admission.snapshot()['attempts'],[])
        self.assertEqual(self.campaign.summary()['finished_jobs'],0)

    def test_changed_path_role_size_and_hash_rejected(self):
        for key,value in [('path','../escape'),('role','video'),('size',True),('sha256','a'*64)]:
            refs=deepcopy(self.refs);refs[0][key]=value
            with self.subTest(key=key):
                with self.assertRaisesRegex(BenchmarkError,'MISMATCH'):
                    self.service.run(self.job,refs)
        self.assertEqual(self.admission.snapshot()['attempts'],[])

    def test_injected_pass_field_rejected(self):
        refs=deepcopy(self.refs);refs[0]['pass']=True
        with self.assertRaisesRegex(BenchmarkError,'FIELDS'):self.service.run(self.job,refs)

    def test_reference_order_is_irrelevant(self):
        with patch('bie.evaluation.benchmarks.native_campaign.runtime.bridge.execute',return_value=self.fake()):
            result=self.service.run(self.job,list(reversed(self.refs)))
        self.assertFalse(result['release_authorized'])

    def test_original_api_run_is_actually_called(self):
        from bie.infrastructure.benchmark_api import BenchmarkAPI
        original=BenchmarkAPI.run;calls=[]
        def traced(obj,case_id,refs):
            calls.append(case_id);return original(obj,case_id,refs)
        with patch.object(BenchmarkAPI,'run',traced):
            self.unit_finished()
        self.assertEqual(calls,[self.job])

    def test_wrong_runtime_and_policy_scope_rejected(self):
        for key in ('runtime_sha256','policy_sha256'):
            cfg=dict(self.configuration);cfg[key]='a'*64
            other=Admission.create(self.root/(key+'.sqlite'),cfg)
            with self.assertRaisesRegex(BenchmarkError,'SCOPE_MISMATCH'):
                Service(self.campaign,self.assets,other)

    def test_wrong_canonical_pin_rejected(self):
        from bie.evaluation.benchmarks.native_api import service
        with patch.dict(service.PIN,{'sha256':'a'*64}):
            with self.assertRaisesRegex(BenchmarkError,'CANONICAL_PIN'):
                self.service.cases()

    def test_ungoverned_native_finished_not_imported(self):
        with patch('bie.evaluation.benchmarks.native_campaign.runtime.bridge.execute',return_value=self.fake()):
            self.campaign.run_job(self.job,self.assets,'outside-api')
        with self.assertRaisesRegex(BenchmarkError,'UNGOVERNED'):
            self.service.run(self.job,self.refs)
        self.assertEqual(self.admission.snapshot()['attempts'],[])


class AdmissionTests(Setup):
    def test_explicit_creation_and_no_overwrite(self):
        before=self.admission.path.read_bytes()
        with self.assertRaisesRegex(BenchmarkError,'ALREADY_EXISTS'):
            Admission.create(self.admission.path,self.configuration)
        self.assertEqual(before,self.admission.path.read_bytes())

    def test_no_implicit_initialization(self):
        with self.assertRaisesRegex(BenchmarkError,'MISSING'):
            Admission(self.root/'missing.sqlite',self.configuration)
        self.assertFalse((self.root/'missing.sqlite').exists())

    def test_deleted_registry_not_recreated(self):
        self.admission.path.unlink()
        with self.assertRaisesRegex(BenchmarkError,'MISSING'):self.service.cases()
        self.assertFalse(self.admission.path.exists())

    def test_sidecar_and_database_symlink_rejected(self):
        for suffix in ('-wal','-shm','-journal'):
            p=Path(str(self.admission.path)+suffix);p.symlink_to(self.root/'absent')
            with self.subTest(suffix=suffix):
                with self.assertRaisesRegex(BenchmarkError,'SYMLINK'):self.admission.snapshot()
            p.unlink()
        self.admission.path.rename(self.root/'original.sqlite')
        self.admission.path.symlink_to(self.root/'original.sqlite')
        with self.assertRaisesRegex(BenchmarkError,'SYMLINK'):self.admission.snapshot()

    def test_hardlinked_database_rejected(self):
        os.link(self.admission.path,self.root/'alias.sqlite')
        with self.assertRaisesRegex(BenchmarkError,'FILE'):self.admission.snapshot()

    def test_context_tampering_rejected(self):
        with sqlite3.connect(self.admission.path) as db:db.execute("UPDATE meta SET v='{}'")
        with self.assertRaisesRegex(BenchmarkError,'CONTEXT_CHANGED'):self.admission.snapshot()

    def test_event_tampering_rejected(self):
        self.admission.reserve(self.plan.effect(self.job),self.plan.sha256,self.job)
        with sqlite3.connect(self.admission.path) as db:db.execute("UPDATE events SET hash=?",('a'*64,))
        with self.assertRaisesRegex(BenchmarkError,'CHAIN'):self.admission.snapshot()

    def test_projection_tampering_rejected(self):
        self.admission.reserve(self.plan.effect(self.job),self.plan.sha256,self.job)
        with sqlite3.connect(self.admission.path) as db:db.execute("UPDATE attempts SET job='injected'")
        with self.assertRaisesRegex(BenchmarkError,'PROJECTION'):self.admission.snapshot()

    def test_unexpected_schema_objects_rejected(self):
        with sqlite3.connect(self.admission.path) as db:db.execute('CREATE TABLE injected(x)')
        with self.assertRaisesRegex(BenchmarkError,'SCHEMA'):self.admission.snapshot()

    def test_reopen_is_identical(self):
        self.unit_finished()
        again=Admission(self.admission.path,self.configuration)
        self.assertEqual(self.admission.snapshot(),again.snapshot())

    def test_cross_campaign_alias_denied_without_execution(self):
        self.unit_finished()
        value=deepcopy(self.value);value['campaign_id']='renamed-campaign'
        plan=Plan(value,digest(value));other=Campaign.create(self.root/'other',plan)
        service=Service(other,self.assets,self.admission)
        with patch('bie.evaluation.benchmarks.native_campaign.runtime.bridge.execute',side_effect=AssertionError('must not run')) as fn:
            with self.assertRaisesRegex(BenchmarkError,'CROSS_CAMPAIGN_DUPLICATE'):
                service.run(self.job,self.refs)
            fn.assert_not_called()
        self.assertEqual(other.summary()['uncompleted_jobs'],1)

    def test_finished_replay_does_not_reexecute(self):
        first=self.unit_finished()
        with patch('bie.evaluation.benchmarks.native_campaign.runtime.bridge.execute',side_effect=AssertionError('must not run')) as fn:
            replay=self.service.run(self.job,self.refs);fn.assert_not_called()
        self.assertTrue(replay['replayed']);self.assertEqual(first['result'],replay['result'])
        self.assertEqual(first['result_sha256'],replay['result_sha256'])

    def test_reserved_attempt_never_retried(self):
        self.admission.reserve(self.plan.effect(self.job),self.plan.sha256,self.job)
        with self.assertRaisesRegex(BenchmarkError,'ATTEMPT_UNAVAILABLE'):
            self.service.run(self.job,self.refs)
        self.assertEqual(self.campaign.summary()['uncompleted_jobs'],1)

    def test_no_result_reconciliation_cannot_manufacture_finish(self):
        self.admission.reserve(self.plan.effect(self.job),self.plan.sha256,self.job)
        with self.assertRaisesRegex(BenchmarkError,'NOT_FINISHED'):
            self.service.runner.reconcile(self.job)
        self.assertEqual(self.admission.snapshot()['attempts'][0]['state'],'RESERVED')

    def test_finish_requires_exact_reservation(self):
        effect=self.plan.effect(self.job)
        with self.assertRaisesRegex(BenchmarkError,'BINDING'):
            self.admission.finish(effect,self.plan.sha256,self.job,'a'*64)
        self.admission.reserve(effect,self.plan.sha256,self.job)
        with self.assertRaisesRegex(BenchmarkError,'BINDING'):
            self.admission.finish(effect,'b'*64,self.job,'a'*64)

    def test_terminal_block_cannot_be_promoted_or_retried(self):
        effect=self.plan.effect(self.job);self.admission.reserve(effect,self.plan.sha256,self.job)
        self.admission.block(effect,self.plan.sha256,self.job,'a'*64,'TEST_INTERRUPTED')
        with self.assertRaisesRegex(BenchmarkError,'TERMINAL'):
            self.admission.finish(effect,self.plan.sha256,self.job,'b'*64)
        with self.assertRaisesRegex(BenchmarkError,'ATTEMPT_UNAVAILABLE'):
            self.service.run(self.job,self.refs)

    def test_failure_keeps_fixed_denominator(self):
        with patch.object(self.campaign,'run_job',side_effect=RuntimeError('unit dispatch failure')):
            with self.assertRaises(RuntimeError):self.service.run(self.job,self.refs)
        summary=self.service.summary()
        self.assertEqual(summary['required_jobs'],1)
        self.assertEqual(summary['jobs'][0]['api_admission_state'],'BLOCKED')
        self.assertEqual(summary['uncompleted_jobs'],1)

    def test_native_completed_registry_crash_window_reconciles(self):
        with patch.object(self.admission,'finish',side_effect=RuntimeError('unit crash-window')):
            with self.assertRaises(RuntimeError):self.unit_finished()
        self.assertEqual(self.admission.snapshot()['attempts'][0]['state'],'RESERVED')
        with patch('bie.evaluation.benchmarks.native_campaign.runtime.bridge.execute',side_effect=AssertionError('no execution')) as fn:
            result=self.service.runner.reconcile(self.job);fn.assert_not_called()
        self.assertTrue(result['reconciled_without_execution'])
        self.assertEqual(self.admission.snapshot()['attempts'][0]['state'],'FINISHED')

    def test_tampered_native_result_not_reconciled(self):
        with patch.object(self.admission,'finish',side_effect=RuntimeError('window')):
            with self.assertRaises(RuntimeError):self.unit_finished()
        resultfile=next(self.campaign.results.glob('*.json'));resultfile.write_bytes(resultfile.read_bytes()+b' ')
        with self.assertRaisesRegex(BenchmarkError,'RESULT_HASH'):
            self.service.runner.reconcile(self.job)
        self.assertEqual(self.admission.snapshot()['attempts'][0]['state'],'RESERVED')


class ActualIntegration(Setup):
    def test_actual_api_collectors_native_qa_and_guard(self):
        result=self.service.run(self.job,self.refs)
        self.assertFalse(result['replayed']);self.assertTrue(result['canonical_api_executed'])
        evaluation=result['result']['evaluation']
        self.assertEqual(set(evaluation['measurement_outcomes'].values()),{'PASS'})
        self.assertTrue(evaluation['native_component_consumer_executed'])
        self.assertEqual(evaluation['native_qa_report']['release_status'],'BLOCKED')
        self.assertEqual(len(evaluation['native_qa_report']['gate_results']),28)
        self.assertEqual(self.admission.snapshot()['attempts'][0]['result_sha256'],result['result_sha256'])

    def test_actual_wrong_frame_and_corrupt_cases(self):
        value=request(self.root/'negative-assets',('wrong-frame','corrupt'))
        plan=Plan(value,digest(value));c=Campaign.create(self.root/'negative-campaign',plan)
        service=Service(c,self.root/'negative-assets',self.admission)
        rows=[service.run(j['job_id'],j['candidate_bundle']['candidate']['artifacts']) for j in value['jobs']]
        self.assertEqual(rows[0]['result']['evaluation']['measurement_outcomes']['BIE-EVAL-METRIC-013'],'FAIL')
        self.assertEqual(set(rows[1]['result']['evaluation']['measurement_outcomes'].values()),{'BLOCKED'})
        self.assertEqual(service.summary()['required_jobs'],2)
        self.assertEqual(service.summary()['finished_jobs'],2)

    def test_actual_changed_source_bytes_blocked(self):
        source=self.assets/self.job/'source.txt';source.write_text('different byte content')
        result=self.service.run(self.job,self.refs)
        self.assertIn('error_code',result['result'])
        self.assertFalse(result['release_authorized'])
        self.assertEqual(self.admission.snapshot()['attempts'][0]['state'],'FINISHED')

    def test_actual_canonical_cli_dispatch_and_replay(self):
        refs=self.root/'refs.json';refs.write_text(canonical_json(self.refs))
        base=[sys.executable,'-B','-m','bie.qa.lifecycle_quality_v2','eval-api']
        common=['--campaign-dir',str(self.campaign.root),'--expected-plan-sha256',self.plan.sha256,
                '--registry',str(self.admission.path),'--scope-id',self.configuration['scope_id'],
                '--artifact-root',str(self.assets)]
        def call(args):
            r=subprocess.run(base+args+common,cwd=ROOT,env=dict(os.environ,PYTHONPATH=str(ROOT),PYTHONDONTWRITEBYTECODE='1'),
                             capture_output=True,text=True,timeout=60)
            self.assertEqual(r.returncode,2,r.stderr)
            value=json.loads(r.stdout);self.assertNotIn('error_code',value);return value
        self.assertEqual(len(call(['cases'])['cases']),1)
        first=call(['run','--case-id',self.job,'--artifact-refs',str(refs)])
        self.assertEqual(set(first['result']['evaluation']['measurement_outcomes'].values()),{'PASS'})
        again=call(['run','--case-id',self.job,'--artifact-refs',str(refs)])
        self.assertTrue(again['replayed']);self.assertEqual(first['result_sha256'],again['result_sha256'])
        self.assertEqual(call(['summary'])['required_jobs'],1)

    def test_actual_competing_process_admission(self):
        script='''import json,sys
from bie.evaluation.benchmarks.native_api.admission import Admission
try:
 a=Admission(sys.argv[1],json.loads(sys.argv[2]));a.reserve(sys.argv[3],sys.argv[4],sys.argv[5]);print('RESERVED')
except Exception as e:
 print(type(e).__name__+':'+str(e));sys.exit(2)
'''
        args=[sys.executable,'-B','-c',script,str(self.admission.path),json.dumps(self.configuration),self.plan.effect(self.job),self.plan.sha256,self.job]
        env=dict(os.environ,PYTHONPATH=str(ROOT),PYTHONDONTWRITEBYTECODE='1')
        children=[subprocess.Popen(args,cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for _ in range(2)]
        outputs=[p.communicate(timeout=30) for p in children]
        self.assertEqual(sorted(p.returncode for p in children),[0,2],outputs)
        self.assertEqual(len(self.admission.snapshot()['attempts']),1)

    def test_actual_interrupted_reservation_remains_counted(self):
        marker=self.root/'reserved.txt'
        script='''import json,sys,time
from pathlib import Path
from bie.evaluation.benchmarks.native_api.admission import Admission
Admission(sys.argv[1],json.loads(sys.argv[2])).reserve(sys.argv[3],sys.argv[4],sys.argv[5])
Path(sys.argv[6]).write_text('committed')
time.sleep(60)
'''
        args=[sys.executable,'-B','-c',script,str(self.admission.path),json.dumps(self.configuration),self.plan.effect(self.job),self.plan.sha256,self.job,str(marker)]
        p=subprocess.Popen(args,cwd=ROOT,env=dict(os.environ,PYTHONPATH=str(ROOT),PYTHONDONTWRITEBYTECODE='1'),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        try:
            end=time.monotonic()+10
            while not marker.exists() and time.monotonic()<end and p.poll() is None:time.sleep(.02)
            self.assertTrue(marker.exists())
        finally:
            p.terminate();p.communicate(timeout=10)
        self.assertNotEqual(p.returncode,0)
        with self.assertRaisesRegex(BenchmarkError,'ATTEMPT_UNAVAILABLE'):
            self.service.run(self.job,self.refs)
        self.assertEqual(self.service.summary()['jobs'][0]['api_admission_state'],'RESERVED')
        self.assertEqual(self.campaign.summary()['uncompleted_jobs'],1)

class AuditRegression(Setup):
    def test_direct_runner_does_not_claim_canonical_api_execution(self):
        with patch('bie.evaluation.benchmarks.native_campaign.runtime.bridge.execute',return_value=self.fake()):
            result=self.service.runner.run(self.job,self.refs)
        self.assertFalse(result['canonical_api_executed'])

    def test_dispatch_exception_receipt_bytes_are_retained(self):
        with patch.object(self.campaign,'run_job',side_effect=RuntimeError('audit fixture')):
            with self.assertRaises(RuntimeError):self.service.run(self.job,self.refs)
        row=self.admission.snapshot()['attempts'][0]
        p=self.campaign.audit/('api-'+row['result_sha256']+'.json')
        self.assertTrue(p.is_file())
        import hashlib
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),row['result_sha256'])
        self.assertEqual(json.loads(p.read_bytes())['error_code'],'API_DISPATCH_EXCEPTION')

    def test_native_replay_race_not_admitted_as_new_execution(self):
        original=Campaign.run_job
        def racing(*args):
            with patch('bie.evaluation.benchmarks.native_campaign.runtime.bridge.execute',return_value=self.fake()):
                original(self.campaign,*args)
                return original(self.campaign,*args)
        with patch.object(self.campaign,'run_job',side_effect=racing):
            with self.assertRaisesRegex(BenchmarkError,'UNGOVERNED_REPLAY'):
                self.service.run(self.job,self.refs)
        self.assertEqual(self.admission.snapshot()['attempts'][0]['state'],'BLOCKED')
