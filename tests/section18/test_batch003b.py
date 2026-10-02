"""QA002/QA004: persisted native evaluator decisions, no supplied UI scores."""
from pathlib import Path
import sys,json,time,secrets,copy,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(Path(__file__).parent))
from test_batch002 import ViewBase
from quality_fixtures import benchmark,execute_release,release_inputs
from apps.operator.quality import Quality,benchmark_projection,release_projection
from apps.operator import quality as module
from apps.operator.contracts import Principal,PERMISSIONS,OperatorError
from apps.operator.service import Service
from bie.evaluation.benchmarks.anti_gaming import AttemptLedger
from bie.evaluation.benchmarks.models import digest,BenchmarkError
from bie.evaluation.benchmarks.release.ledger import ReleaseLedger
from bie.evaluation.benchmarks.release import gate

class QualityBase(ViewBase):
    def setUp(self):
        super().setUp();self.q=Quality(self.service);self.resources=[]
    def tearDown(self):
        for r in reversed(self.resources):r.close()
        super().tearDown()
    def bench(self,answers=None):
        registry,self.ledger,self.snapshot,self.native_result=benchmark(self.root,self.body,answers)
        self.resources.append(registry);return self.native_result
    def bpublish(self,**kwargs):
        options=dict(evidence_origin='SYNTHETIC_TEST');options.update(kwargs)
        return self.q.bind_benchmark(self.p,self.run,self.ref,self.ledger,self.body['native_job_id'],self.snapshot,**options)
    def release(self,mutator=None,production=False,attempt='release-1',campaign='release-campaign'):
        self.rl,self.manifest,self.policy=execute_release(self.root,self.body,mutator,production,attempt,campaign)
        self.resources.append(self.rl);return self.rl.get(attempt)
    def rpublish(self,attempt='release-1',**kwargs):
        options=dict(evidence_origin='SYNTHETIC_TEST');options.update(kwargs)
        return self.q.bind_release(self.p,self.run,self.ref,self.rl,attempt,self.manifest,self.policy,**options)
    def first(self,kind):return self.q.get(self.p,self.run,kind)['items'][0]
    def qhttp(self,kind):return self.get('runs/'+self.run+'/quality/'+kind)

class Qa002(QualityBase):
    def test_actual_canonical_structured_grading_receipt(self):
        r=self.bench();v=self.bpublish()['view'];self.assertEqual(v['status'],r['report']['status']);self.assertEqual(v['score'],'1')
    def test_canonical_ledger_get_report_actually_called(self):
        self.bench()
        with patch.object(AttemptLedger,'get_report',autospec=True,side_effect=lambda ledger,r: self.native_result['report']) as read:self.bpublish()
        read.assert_called_once_with(self.ledger,self.body['native_job_id'])
    def test_missing_cases_count_in_frozen_denominator(self):
        self.bench([dict(case_id='case-1',output={'value':1})]);v=self.bpublish()['view']
        self.assertEqual(v['denominator'],2);self.assertEqual(v['status'],'FAIL');self.assertEqual(v['score'],'1/2');self.assertEqual(v['missing_case_ids'],['case-2'])
    def test_missing_all_results_is_zero_not_success(self):
        self.bench([]);v=self.bpublish()['view'];self.assertEqual(v['score'],'0');self.assertEqual(v['measured_coverage'],'0');self.assertEqual(v['status'],'FAIL')
    def test_bad_candidate_answers_do_not_get_invented_score(self):
        self.bench([dict(case_id='case-1',output={'value':True}),dict(case_id='case-2',output={'value':'2'})]);self.assertEqual(self.bpublish()['view']['passed_count'],0)
    def test_raw_answers_and_reference_payloads_not_exposed(self):
        self.bench();self.bpublish();wire=self.qhttp('benchmark').text
        for word in ('expected_json','inputs_json','prompt','derivation','source_bytes','golden_answers','output'):self.assertNotIn('"'+word+'"',wire)
    def test_dataset_identity_and_version_are_exact(self):
        self.bench();d=self.bpublish()['view']['dataset'];self.assertEqual(d['sha256'],self.snapshot.sha256);self.assertEqual(d['version'],'1.0.0')
    def test_live_assessment_and_acceptance_not_fabricated(self):
        self.bench();v=self.bpublish()['view'];self.assertEqual(v['live_assessor_status'],'NOT_RUN');self.assertFalse(v['golden_benchmark_certified']);self.assertFalse(v['product_accepted'])
    def test_no_fixture_substitution_when_no_native_receipt(self):
        self.assertEqual(self.qhttp('benchmark').json()['status'],'NOT_RUN');self.assertEqual(self.qhttp('benchmark').json()['items'],[])
    def test_replay_and_operator_restart_identical(self):
        self.bench();a=self.bpublish();self.assertEqual(a,self.bpublish())
        self.assertEqual(a,Quality(Service(self.root,self.creds)).get(self.p,self.run,'benchmark')['items'][0])
        from bie.evaluation.benchmarks.registry import Registry
        with Registry(self.root/'benchmark.sqlite3') as r:self.assertEqual(AttemptLedger(r).get_report(self.body['native_job_id']),self.native_result['report'])
    def test_boolean_received_count_is_not_integer_one(self):
        self.bench([dict(case_id='case-1',output={'value':1})]);r=copy.deepcopy(self.native_result['report']);r['received_count']=True
        self.error(lambda:benchmark_projection(r,self.snapshot),'quality_count_invalid')
    def test_native_report_checksum_tamper_rejected(self):
        self.bench();self.ledger.registry.connection.execute("UPDATE attempts SET report_sha=?",('0'*64,))
        self.error(self.bpublish,'native_benchmark_receipt_invalid')
    def test_native_roster_tamper_rejected(self):
        self.bench();self.ledger.registry.connection.execute("UPDATE attempts SET roster_json='[]'")
        self.error(self.bpublish,'native_benchmark_receipt_invalid')
    def test_candidate_binding_mismatch_rejected(self):
        self.bench();self.native_result['report']['binding']['candidate_sha256']='0'*64
        with patch.object(AttemptLedger,'get_report',return_value=self.native_result['report']):self.error(self.bpublish,'quality_candidate_mismatch')
    def test_other_native_run_never_attached(self):
        self.bench();self.native_result['report']['binding']['run_id']='other-run'
        with patch.object(AttemptLedger,'get_report',return_value=self.native_result['report']):self.error(self.bpublish,'quality_run_binding_mismatch')
    def test_projection_rechecks_denominator_even_if_checksum_recomputed(self):
        self.bench();r=copy.deepcopy(self.native_result['report']);r['denominator']=1
        self.error(lambda:benchmark_projection(r,self.snapshot),'quality_denominator_invalid')
    def test_projection_rejects_unauthorized_product_promotion(self):
        self.bench();r=copy.deepcopy(self.native_result['report']);r['product_accepted']=True
        self.error(lambda:benchmark_projection(r,self.snapshot),'quality_unauthorized_promotion')
    def test_no_arbitrary_json_ledger_accepted(self):
        self.bench();self.ledger={};self.error(self.bpublish,'native_ledger_required')
    def test_cross_tenant_cannot_read_snapshot(self):
        self.bench();self.bpublish();self.error(lambda:self.q.get(self.foreign(),self.run,'benchmark'),'run_not_found')
    def test_revoked_credentials_remove_access(self):
        self.bench();self.bpublish();self.creds.revoke(self.token);self.assertEqual(self.qhttp('benchmark').status_code,401)
    def test_expired_credentials_remove_access(self):
        self.bench();self.bpublish();self.creds.grant(self.token,Principal(self.p.actor,self.p.tenant,PERMISSIONS,time.time()-1));self.assertEqual(self.qhttp('benchmark').status_code,401)
    def test_reader_cannot_publish(self):
        self.bench();p=Principal('reader','tenant-a',frozenset({'read'}),time.time()+100);self.creds.grant(secrets.token_hex(32),p)
        self.error(lambda:self.q.bind_benchmark(p,self.run,self.ref,self.ledger,self.body['native_job_id'],self.snapshot,evidence_origin='SYNTHETIC_TEST'),'forbidden')
    def test_cas_tamper_fails_closed(self):
        self.bench();aid=self.bpublish()['artifact_id'];self.tamper_blob(aid);self.assertEqual(self.qhttp('benchmark').status_code,500)
    def test_parent_source_tamper_fails_closed(self):
        self.bench();self.bpublish();self.tamper_blob(self.ref);self.assertEqual(self.qhttp('benchmark').status_code,500)
    def test_http_read_only_no_score_publication(self):
        self.bench();self.bpublish();self.assertEqual(self.post('runs/'+self.run+'/quality/benchmark',{'score':1}).status_code,405)
    def test_pagination_strict_not_unbounded(self):
        for offset,limit in ((-1,1),(0,0),(0,101),(True,2)):
            with self.subTest(offset=offset):self.error(lambda:self.q.get(self.p,self.run,'benchmark',offset,limit),'invalid_pagination')
    def test_http_no_paths_secrets_or_cors(self):
        self.bench();self.bpublish();r=self.qhttp('benchmark');self.assertEqual(r.status_code,200);self.assertNotIn(str(self.root),r.text);self.assertNotIn(self.token,r.text);self.assertNotIn('access-control-allow-origin',r.headers)

class Qa004(QualityBase):
    def test_canonical_release_gate_executes_before_projection(self):
        with patch.object(gate,'evaluate',wraps=gate.evaluate) as evaluate:self.release()
        self.assertEqual(evaluate.call_count,1);self.assertEqual(self.rpublish()['view']['outcome'],'DIAGNOSTIC_PASS')
    def test_canonical_release_ledger_get_actually_called(self):
        receipt=self.release()
        with patch.object(ReleaseLedger,'get',autospec=True,side_effect=lambda ledger,a:receipt) as read:self.rpublish()
        read.assert_called_once_with(self.rl,'release-1')
    def test_diagnostic_pass_is_never_release_authority(self):
        self.release();v=self.rpublish()['view'];self.assertFalse(v['benchmark_gate_passed']);self.assertFalse(v['release_authorized']);self.assertFalse(v['current_deployment_authority'])
    def test_missing_raters_and_measurements_block(self):
        self.release(lambda m,p,a:a.clear());v=self.rpublish()['view'];self.assertEqual(v['outcome'],'BLOCKED');self.assertTrue(v['reasons']);self.assertTrue(all(x['status']=='BLOCKED' for x in v['metric_rows']))
    def test_critical_floor_not_overridden_by_other_high_scores(self):
        def low(m,p,a):
            for r in a[:2]:r['score_exact']='0';r['assessment_sha256']=digest({k:v for k,v in r.items() if k!='assessment_sha256'})
        self.release(low);v=self.rpublish()['view'];self.assertEqual(v['outcome'],'BLOCKED');self.assertIn('CRITICAL_HARD_FLOOR_BREACHED',v['reasons'])
    def test_domain_floors_displayed_from_frozen_policy(self):
        self.release();v=self.rpublish()['view'];self.assertEqual({d['domain'] for d in v['domain_floors']},{'math','physics'});self.assertTrue(all(d['minimum_measured_fraction']=='1' for d in v['domain_floors']))
    def test_agreement_undefined_kappa_not_perfect(self):
        self.release();v=self.rpublish()['view']['agreement'][0];self.assertIsNone(v['kappa']);self.assertEqual(v['kappa_state'],'UNDEFINED');self.assertEqual(v['pair'],'det / human')
    def test_required_agreement_can_block(self):
        self.release(lambda m,p,a:p['agreement'].update(minimum_kappa='1/2'));self.assertIn('KAPPA_REQUIREMENT_NOT_MET',self.rpublish()['view']['reasons'])
    def test_production_missing_external_evidence_blocks(self):
        self.release(production=True);v=self.rpublish()['view'];self.assertEqual(v['outcome'],'BLOCKED');self.assertIn('MISSING_NATIVE_BOOK_E2E',v['reasons']);self.assertFalse(v['product_accepted'])
    def test_invalid_production_policy_remains_retained_blocked(self):
        self.release(lambda m,p,a:p.update(mode='PRODUCTION'));v=self.rpublish()['view'];self.assertEqual(v['outcome'],'BLOCKED');self.assertIn('PRODUCTION_ATTESTATION_POLICY_WEAKENED',v['reasons'])
    def test_missing_release_receipt_explicit_not_run(self):self.assertEqual(self.qhttp('release').json()['status'],'NOT_RUN')
    def test_failed_attempt_is_not_overwritten_or_erased(self):
        self.release(lambda m,p,a:a.clear());self.rpublish()
        with self.assertRaises(BenchmarkError):self.rl.execute(campaign_id='release-campaign',attempt_id='retry',manifest=self.manifest,policy=self.policy,assessments=[],expected_manifest_sha256=digest(self.manifest),expected_policy_sha256=digest(self.policy))
        self.assertEqual(self.first('release')['view']['outcome'],'BLOCKED')
    def test_restart_and_replay_keep_same_snapshot(self):
        self.release();a=self.rpublish();self.assertEqual(a,self.rpublish());self.assertEqual(a,Quality(Service(self.root,self.creds)).get(self.p,self.run,'release')['items'][0])
    def test_native_ledger_reopen_verifies_receipt(self):
        r=self.release()
        with ReleaseLedger(self.root/'release.sqlite3') as l:self.assertEqual(l.get('release-1'),r)
    def test_changed_manifest_not_accepted_as_same_receipt(self):
        self.release();self.manifest['version']='1.0.1';self.error(self.rpublish,'quality_release_pins_mismatch')
    def test_changed_policy_not_silently_activated(self):
        self.release();self.policy['version']='1.0.1';self.error(self.rpublish,'quality_release_pins_mismatch')
    def test_candidate_artifact_mismatch_rejected(self):
        self.body['source_hash']='0'*64;self.release();self.error(self.rpublish,'quality_candidate_mismatch')
    def test_cross_run_context_rejected(self):
        def changed(m,p,a):
            for r in m['cases']:r['context']['run_id']='other-run'
            for r in a:r['context']['run_id']='other-run';r['assessment_sha256']=digest({k:v for k,v in r.items() if k!='assessment_sha256'})
        self.release(changed);self.error(self.rpublish,'quality_run_binding_mismatch')
    def test_native_receipt_tamper_rejected(self):
        self.release();self.rl.db.execute("UPDATE release_attempts SET receipt='{}'");self.error(self.rpublish,'native_release_receipt_invalid')
    def test_native_campaign_tamper_rejected(self):
        self.release();self.rl.db.execute("UPDATE release_campaigns SET binding='{}'");self.error(self.rpublish,'native_release_receipt_invalid')
    def test_incomplete_attempt_never_available(self):
        self.release();self.rl.db.execute("UPDATE release_attempts SET state='RUNNING'");self.error(self.rpublish,'native_release_receipt_invalid')
    def test_different_campaign_history_is_paginated_not_discarded(self):
        self.release();self.rpublish();self.release(attempt='release-2',campaign='campaign-2');self.rpublish('release-2')
        v=self.q.get(self.p,self.run,'release',0,1);self.assertEqual(v['total'],2);self.assertEqual(v['next_offset'],1)
        self.assertIsNone(self.q.get(self.p,self.run,'release',1,1)['next_offset'])
    def test_history_cap_not_unbounded(self):
        self.release();self.rpublish();self.release(attempt='release-2',campaign='campaign-2')
        with patch.object(module,'MAX_HISTORY',1):self.error(lambda:self.rpublish('release-2'),'quality_history_limit')
    def test_partial_index_interruption_recovers_same_native_receipt(self):
        self.release()
        with patch.object(self.service.catalog,'event',side_effect=RuntimeError('seeded_interruption')):
            with self.assertRaises(RuntimeError):self.rpublish()
        self.assertEqual(self.rpublish()['integrity'],'VERIFIED')
    def test_cross_tenant_is_not_found(self):
        self.release();self.rpublish();self.error(lambda:self.q.get(self.foreign(),self.run,'release'),'run_not_found')
    def test_cas_and_record_seal_tamper_fail_closed(self):
        self.release();aid=self.rpublish()['artifact_id'];self.tamper_blob(aid);self.assertEqual(self.qhttp('release').status_code,500)
    def test_no_release_action_route_or_raw_assessments(self):
        self.release();self.rpublish();r=self.qhttp('release');self.assertEqual(r.status_code,200)
        for k in ('assessments','signature','secret','rationale','traceback'):self.assertNotIn('"'+k+'"',r.text)
        self.assertEqual(self.post('runs/'+self.run+'/quality/release',{'release_authorized':True}).status_code,405)
    def test_unknown_quality_kind_no_fallback(self):self.error(lambda:self.q.get(self.p,self.run,'qa'),'quality_kind_unavailable')

TASK_CLASSES={'BIE-APP-QA-002':Qa002,'BIE-APP-QA-004':Qa004}
def selected_suite(task=None):
    suite=unittest.TestSuite()
    for key,cls in TASK_CLASSES.items():
        if task is None or task==key:
            for method in sorted(cls.__dict__):
                if method.startswith('test_'):suite.addTest(cls(method))
    return suite
if __name__=='__main__':unittest.TextTestRunner(verbosity=2).run(selected_suite())
