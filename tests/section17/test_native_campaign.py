"""Campaign contract, journal, real CLI and actual AV integration tests.

Orchestration fault tests explicitly mock the bridge. RealIntegration executes it.
Subtests and repeated runs are not additional method IDs.
"""
from copy import deepcopy
from dataclasses import FrozenInstanceError, asdict
import hashlib
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

from native_campaign_support import request, plan
from native_qa_support import positive
from bie.evaluation.benchmarks.models import digest, canonical_json, BenchmarkError
from bie.evaluation.benchmarks.native_campaign.contracts import Plan, runtime_digest, verify_native_core
from bie.evaluation.benchmarks.native_campaign.runtime import Campaign

ROOT=Path(__file__).resolve().parents[2]

class Case(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='bie-campaign-test-');self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.assets=self.root/'assets'
        self.value=request(self.assets)
    def build(self):return Plan(self.value,digest(self.value))
    def campaign(self):return Campaign.create(self.root/'campaign',self.build())
    def fake(self):
        # Unit-only orchestration payload, NEVER counted as an AV diagnostic.
        return {'release_authorized':False,'product_accepted':False,'native_qa_report':{'release_status':'BLOCKED'},
                'measurement_outcomes':{'fixture':'PASS'},'native_component_consumer_executed':False}
    def finished(self):
        c=self.campaign()
        with patch('bie.evaluation.benchmarks.native_campaign.runtime.bridge.execute',return_value=self.fake()):
            r=c.run_job(self.value['jobs'][0]['job_id'],self.assets,'unit-worker')
        return c,r

class Contracts(Case):
    def test_exact_native_core_matches(self):verify_native_core()
    def test_plan_wrong_external_pin(self):
        with self.assertRaisesRegex(BenchmarkError,'PLAN_PIN'):Plan(self.value,'a'*64)
    def test_plan_unknown_field(self):
        self.value['release_authorized']=True
        with self.assertRaisesRegex(BenchmarkError,'PLAN_FIELDS'):self.build()
    def test_wrong_schema(self):
        self.value['schema_version']='bad'
        with self.assertRaisesRegex(BenchmarkError,'SCHEMA'):self.build()
    def test_wrong_revision(self):
        self.value['revision']='a'*40
        with self.assertRaisesRegex(BenchmarkError,'REVISION'):self.build()
    def test_changed_policy(self):
        self.value['policy_sha256']='a'*64
        with self.assertRaisesRegex(BenchmarkError,'POLICY_PIN'):self.build()
    def test_empty_and_oversized_roster(self):
        for jobs in ([],self.value['jobs']*129):
            with self.subTest(count=len(jobs)):
                v=deepcopy(self.value);v['jobs']=jobs
                with self.assertRaisesRegex(BenchmarkError,'ROSTER_COUNT'):Plan(v,digest(v))
    def test_duplicate_job_id(self):
        self.value['jobs']*=2
        with self.assertRaisesRegex(BenchmarkError,'DUPLICATE_JOB'):self.build()
    def test_renamed_identical_candidate_rejected(self):
        other=deepcopy(self.value['jobs'][0]);other['job_id']='alias';other['artifact_subdir']='alias'
        # Candidate/run IDs are labels, not new content.
        other['candidate_bundle']['candidate']['candidate_id']='alias-candidate'
        other['candidate_bundle']['candidate']['run_id']='alias-run'
        from bie.qa.release_v2.codec import bundle_from_dict
        other['expected_candidate_digest']=bundle_from_dict(other['candidate_bundle']).candidate.content_digest
        self.value['jobs'].append(other)
        with self.assertRaisesRegex(BenchmarkError,'CONTENT_ALIAS'):self.build()
    def test_wrong_candidate_pin(self):
        self.value['jobs'][0]['expected_candidate_digest']='a'*64
        with self.assertRaisesRegex(BenchmarkError,'CANDIDATE_PIN'):self.build()
    def test_wrong_checks_pin(self):
        self.value['jobs'][0]['expected_checks_digest']='a'*64
        with self.assertRaisesRegex(BenchmarkError,'CHECKS_PIN'):self.build()
    def test_unsafe_artifact_subdirectory(self):
        for path in ('../outside','/tmp/outside','a/../../b'):
            with self.subTest(path=path):
                v=deepcopy(self.value);v['jobs'][0]['artifact_subdir']=path
                with self.assertRaises(ValueError):Plan(v,digest(v))
    def test_no_empty_av_subset(self):
        self.value['jobs'][0]['checks']=[];self.value['jobs'][0]['expected_checks_digest']=digest([])
        with self.assertRaisesRegex(BenchmarkError,'REQUIRED_AV_ROSTER'):self.build()
    def test_extra_candidate_fields_rejected(self):
        self.value['jobs'][0]['candidate_bundle']['pass']=True
        with self.assertRaises(ValueError):self.build()
    def test_limits_must_be_complete(self):
        self.value['limits'].pop('deadline_s')
        with self.assertRaisesRegex(BenchmarkError,'EXPLICIT_LIMITS'):self.build()
    def test_repeated_attempt_budget_disallowed(self):
        self.value['lease_policy']['attempts']=2
        with self.assertRaisesRegex(BenchmarkError,'SINGLE_ATTEMPT'):self.build()
    def test_too_short_lease_rejected(self):
        self.value['lease_policy']['lease_seconds']=40
        with self.assertRaisesRegex(BenchmarkError,'LEASE_BUDGET'):self.build()
    def test_input_and_output_plan_detached(self):
        p=self.build();self.value['jobs'].clear();v=p.data();v['jobs'].clear()
        self.assertEqual(len(p.data()['jobs']),1)
        with self.assertRaises(FrozenInstanceError):p.sha256='a'*64
    def test_unknown_job(self):
        with self.assertRaisesRegex(BenchmarkError,'UNKNOWN_JOB'):self.build().job('unknown')

class Persistence(Case):
    def test_initial_roster_denominator(self):
        self.value=request(self.assets,('good','wrong-frame','corrupt'))
        s=self.campaign().summary();self.assertEqual(s['required_jobs'],3);self.assertEqual(s['uncompleted_jobs'],3)
        self.assertEqual([j['state'] for j in s['jobs']],['NOT_RUN']*3)
    def test_reopen_preserves_plan_and_native_journal(self):
        c=self.campaign();again=Campaign(c.root,c.plan);self.assertEqual(c.summary(),again.summary())
    def test_create_never_overwrites(self):
        c=self.campaign()
        with self.assertRaises(FileExistsError):Campaign.create(c.root,c.plan)
    def test_changed_stored_plan_rejected(self):
        c=self.campaign();(c.root/'PLAN.json').write_text('{}')
        with self.assertRaisesRegex(BenchmarkError,'STORED_PLAN_CHANGED'):c.summary()
    def test_missing_database_not_reinitialized(self):
        c=self.campaign();(c.root/'campaign.sqlite').unlink()
        with self.assertRaisesRegex(BenchmarkError,'DATABASE_MISSING'):Campaign(c.root,c.plan)
    def test_database_sidecar_symlink_rejected(self):
        c=self.campaign();outside=self.root/'outside';outside.write_text('untouched')
        (c.root/'campaign.sqlite-wal').symlink_to(outside)
        with self.assertRaisesRegex(BenchmarkError,'DATABASE_SYMLINK'):c.summary()
        self.assertEqual(outside.read_text(),'untouched')
    def test_result_directory_symlink_rejected(self):
        c=self.campaign();c.results.rmdir();c.results.symlink_to(self.assets)
        with self.assertRaisesRegex(BenchmarkError,'DIRECTORY_SYMLINK'):c.summary()
    def test_runtime_pin_mismatch_before_initialization(self):
        self.value['runtime_sha256']='a'*64
        with self.assertRaisesRegex(BenchmarkError,'RUNTIME_CHANGED'):self.campaign()
        self.assertFalse((self.root/'campaign').exists())
    def test_finished_means_blocked_not_release(self):
        c,r=self.finished();s=c.summary()
        self.assertEqual(s['finished_jobs'],1);self.assertEqual(s['status'],'BLOCKED')
        self.assertFalse(s['release_authorized']);self.assertEqual(s['outbox_count'],1)
    def test_replay_does_not_execute_again(self):
        c,r=self.finished()
        with patch('bie.evaluation.benchmarks.native_campaign.runtime.bridge.execute',side_effect=AssertionError('rerun')) as fn:
            replay=c.run_job(self.value['jobs'][0]['job_id'],self.assets,'different-worker')
        self.assertTrue(replay['replayed']);fn.assert_not_called();self.assertEqual(r['result'],replay['result'])
    def test_missing_result_not_recomputed(self):
        c,r=self.finished();next(c.results.glob('*.json')).unlink()
        with self.assertRaises(FileNotFoundError):c.summary()
    def test_result_bytes_tampering_rejected(self):
        c,r=self.finished();p=next(c.results.glob('*.json'));p.write_bytes(p.read_bytes()+b' ')
        with self.assertRaisesRegex(BenchmarkError,'RESULT_HASH'):c.summary()
    def test_native_projection_tampering_rejected(self):
        c=self.campaign()
        with sqlite3.connect(c.root/'campaign.sqlite') as db:
            db.execute("INSERT INTO jobs VALUES('unregistered',?,'RUNNING',1,1,'bad',100,1,NULL)",('a'*64,))
        with self.assertRaises(ValueError):c.summary()
    def test_collector_exception_becomes_terminal_blocked(self):
        c=self.campaign()
        with patch('bie.evaluation.benchmarks.native_campaign.runtime.bridge.execute',side_effect=RuntimeError('fixture exception')):
            row=c.run_job(self.value['jobs'][0]['job_id'],self.assets,'worker')
        self.assertEqual(row['result']['error_code'],'CAMPAIGN_EXECUTION_EXCEPTION')
        self.assertEqual(c.summary()['finished_jobs'],1)
    def test_injected_positive_upstream_cannot_authorize(self):
        c=self.campaign();fake=self.fake();fake['release_authorized']=True
        with patch('bie.evaluation.benchmarks.native_campaign.runtime.bridge.execute',return_value=fake):
            row=c.run_job(self.value['jobs'][0]['job_id'],self.assets,'worker')
        self.assertEqual(row['result']['error_code'],'CAMPAIGN_UPSTREAM_PROMOTION')
        self.assertFalse(row['result']['release_authorized'])
    def test_missing_artifact_folder_is_recorded(self):
        c=self.campaign();row=c.run_job(self.value['jobs'][0]['job_id'],self.root/'absent','worker')
        self.assertEqual(row['result']['error_code'],'CAMPAIGN_DIRECTORY_REQUIRED')
        self.assertEqual(c.summary()['finished_jobs'],1)
    def test_active_lease_blocks_second_worker(self):
        c=self.campaign();j=self.value['jobs'][0]['job_id'];c.journal.claim(j,c.plan.effect(j),'owner',int(time.time()))
        with self.assertRaisesRegex(ValueError,'LEASE_BUSY'):c.run_job(j,self.assets,'other')
    def test_expired_lease_does_not_mint_retry(self):
        c=self.campaign();j=self.value['jobs'][0]['job_id'];c.journal.claim(j,c.plan.effect(j),'owner',int(time.time())-300)
        with self.assertRaisesRegex(ValueError,'ATTEMPT_BUDGET'):c.run_job(j,self.assets,'other')
        self.assertEqual(c.summary()['uncompleted_jobs'],1)
    def test_cancel_fences_old_worker_and_retains_denominator(self):
        c=self.campaign();j=self.value['jobs'][0]['job_id'];now=int(time.time());r=c.journal.claim(j,c.plan.effect(j),'owner',now)
        s=c.cancel(j);self.assertEqual(s['jobs'][0]['state'],'CANCELLED');self.assertEqual(s['required_jobs'],1)
        with self.assertRaisesRegex(ValueError,'STALE_FENCE'):c.journal.finish(j,r['token'],'owner',now,'a'*64,('summary',))
    def test_cancelled_job_never_replays(self):
        c=self.campaign();j=self.value['jobs'][0]['job_id'];c.journal.claim(j,c.plan.effect(j),'owner',int(time.time()));c.cancel(j)
        with self.assertRaisesRegex(ValueError,'JOB_CANCELLED'):c.run_job(j,self.assets,'owner')
    def test_result_saved_but_finish_failure_is_not_complete(self):
        c=self.campaign();j=self.value['jobs'][0]['job_id']
        with patch('bie.evaluation.benchmarks.native_campaign.runtime.bridge.execute',return_value=self.fake()),patch.object(c.journal,'finish',side_effect=RuntimeError('crash before commit')):
            with self.assertRaises(RuntimeError):c.run_job(j,self.assets,'owner')
        self.assertEqual(len(list(c.results.glob('*.json'))),1)
        self.assertEqual(c.summary()['uncompleted_jobs'],1)
        self.assertEqual(c.summary()['outbox_count'],0)
    def test_partial_campaign_does_not_drop_unrun_cases(self):
        self.value=request(self.assets,('good','wrong-frame'))
        c=self.campaign()
        with patch('bie.evaluation.benchmarks.native_campaign.runtime.bridge.execute',return_value=self.fake()):
            c.run_job(self.value['jobs'][0]['job_id'],self.assets,'worker')
        s=c.summary();self.assertEqual(s['required_jobs'],2);self.assertEqual(s['finished_jobs'],1);self.assertEqual(s['uncompleted_jobs'],1)

class RealIntegration(Case):
    def test_actual_native_av_and_journal_round_trip(self):
        c=self.campaign();result=c.run_job(self.value['jobs'][0]['job_id'],self.assets,'actual-worker')['result']
        self.assertNotIn('error_code',result)
        evaluation=result['evaluation'];self.assertEqual(set(evaluation['measurement_outcomes'].values()),{'PASS'})
        self.assertTrue(evaluation['native_component_consumer_executed'])
        self.assertEqual(evaluation['native_qa_report']['release_status'],'BLOCKED')
        self.assertEqual(len(evaluation['native_qa_report']['gate_results']),28)
        self.assertEqual(c.summary(),Campaign(c.root,c.plan).summary())
    def test_actual_wrong_frame_and_corrupt_controls(self):
        self.value=request(self.assets,('wrong-frame','corrupt'));c=self.campaign()
        result=c.run(self.assets,'actual-worker');s=result['summary'];self.assertEqual(s['finished_jobs'],2)
        self.assertEqual(s['jobs'][0]['measurement_outcomes']['BIE-EVAL-METRIC-013'],'FAIL')
        self.assertEqual(set(s['jobs'][1]['measurement_outcomes'].values()),{'BLOCKED'})
    def test_actual_canonical_cli_init_run_and_replay(self):
        planpath=self.root/'request.json';planpath.write_text(canonical_json(self.value));root=self.root/'cli'
        base=[sys.executable,'-B','-m','bie.qa.lifecycle_quality_v2','eval-campaign']
        common=['--campaign-dir',str(root),'--expected-plan-sha256',digest(self.value)]
        env=dict(os.environ,PYTHONPATH=str(ROOT),PYTHONDONTWRITEBYTECODE='1')
        def call(args):
            r=subprocess.run(base+args+common,cwd=ROOT,env=env,capture_output=True,text=True,timeout=60)
            self.assertEqual(r.returncode,2,r.stderr);return json.loads(r.stdout)
        initialized=call(['init','--plan',str(planpath)]);self.assertNotIn('error_code',initialized)
        result=call(['run','--artifact-root',str(self.assets)]);self.assertEqual(result['summary']['finished_jobs'],1)
        self.assertEqual(set(result['summary']['jobs'][0]['measurement_outcomes'].values()),{'PASS'})
        replay=call(['run','--artifact-root',str(self.assets)]);self.assertTrue(replay['dispatch'][0]['replayed'])
        self.assertEqual(result['summary'],replay['summary'])
    def test_existing_canonical_journal_cli_preserved(self):
        c=self.campaign();context=self.root/'context.json';context.write_text(json.dumps({'binding':asdict(c.journal.binding),'policy':asdict(c.policy)}))
        r=subprocess.run([sys.executable,'-B','-m','bie.qa.lifecycle_quality_v2',str(c.root/'campaign.sqlite'),'--context',str(context)],
            cwd=ROOT,env=dict(os.environ,PYTHONPATH=str(ROOT)),capture_output=True,text=True,timeout=30)
        self.assertEqual(r.returncode,0,r.stderr);self.assertFalse(json.loads(r.stdout)['product_accepted'])
    def test_actual_competing_processes_one_claim(self):
        c=self.campaign();j=self.value['jobs'][0]['job_id']
        script='''import sys,json,time
from bie.evaluation.benchmarks.native_campaign import Plan,Campaign
from bie.evaluation.benchmarks.models import strict_loads
from pathlib import Path
p=Path(sys.argv[1]);plan=Plan(strict_loads((p/'PLAN.json').read_bytes()),sys.argv[2]);c=Campaign(p,plan)
try:
 print(json.dumps(c.journal.claim(sys.argv[3],plan.effect(sys.argv[3]),sys.argv[4],int(time.time()))))
except Exception as e:
 print(json.dumps({'error':getattr(e,'code',str(e))}));sys.exit(2)
'''
        ps=[subprocess.Popen([sys.executable,'-B','-c',script,str(c.root),c.plan.sha256,j,owner],cwd=ROOT,
            env=dict(os.environ,PYTHONPATH=str(ROOT)),stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            for owner in ('worker-one','worker-two')]
        logs=[p.communicate(timeout=30) for p in ps]
        self.assertEqual(sorted(p.returncode for p in ps),[0,2],logs)
        self.assertEqual(c.journal.export()['jobs'][0]['attempts'],1)


class AuditRegression(Case):
    def test_all_artifact_path_aliases_still_one_effect(self):
        other=deepcopy(self.value['jobs'][0]);other['job_id']='renamed';other['artifact_subdir']='renamed'
        c=other['candidate_bundle']['candidate'];c['candidate_id']='renamed';c['run_id']='renamed'
        renames={a['path']:'nested/'+a['path'] for a in c['artifacts']}
        for a in c['artifacts']:a['path']=renames[a['path']]
        for row in other['checks']:
            for field in ('media','captions'):
                if row['candidate'][field]:row['candidate'][field]['path']=renames[row['candidate'][field]['path']]
            row['expected_candidate_sha256']=digest(row['candidate'])
        from bie.qa.release_v2.codec import bundle_from_dict
        other['expected_candidate_digest']=bundle_from_dict(other['candidate_bundle']).candidate.content_digest
        other['expected_checks_digest']=digest(other['checks']);self.value['jobs'].append(other)
        with self.assertRaisesRegex(BenchmarkError,'CONTENT_ALIAS'):self.build()
    def test_database_hardlink_is_not_trusted(self):
        c=self.campaign();os.link(c.root/'campaign.sqlite',self.root/'second-name')
        with self.assertRaisesRegex(BenchmarkError,'DATABASE_FILE'):c.summary()
    def test_result_hardlink_rejected(self):
        c,_=self.finished();result=next(c.results.glob('*.json'));os.link(result,self.root/'leak')
        with self.assertRaisesRegex(BenchmarkError,'NOT_REGULAR'):c.summary()
    def test_public_data_mutation_cannot_change_roster(self):
        c=self.campaign();d=c.data;d['jobs'].clear()
        self.assertEqual(c.summary()['required_jobs'],1)
    def test_manifest_race_after_claim_cannot_finish(self):
        c=self.campaign();j=self.value['jobs'][0]['job_id']
        def corrupt(*args,**kwargs):
            (c.root/'PLAN.json').write_text('{}');return self.fake()
        with patch('bie.evaluation.benchmarks.native_campaign.runtime.bridge.execute',side_effect=corrupt):
            with self.assertRaisesRegex(BenchmarkError,'STORED_PLAN_CHANGED'):c.run_job(j,self.assets,'worker')
        self.assertEqual(c.journal.export()['jobs'][0]['state'],'RUNNING')
        self.assertEqual(c.journal.pending(),[])
    def test_registry_count_remains_fixed_after_dispatch_failure(self):
        self.value=request(self.assets,('good','wrong-frame'));c=self.campaign()
        with patch.object(c,'run_job',side_effect=RuntimeError('operator diagnostic')):
            result=c.run(self.assets,'worker')
        self.assertEqual(len(result['dispatch']),2);self.assertEqual(result['summary']['required_jobs'],2)
        self.assertEqual(result['summary']['uncompleted_jobs'],2)

if __name__=='__main__':unittest.main()
