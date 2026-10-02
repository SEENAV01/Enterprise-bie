"""QA001 native fail-closed gate adapter; QA003 local projection, not native proof."""
import copy,json,time,secrets,unittest,sys,os
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(Path(__file__).parent))
from test_batch002 import ViewBase
from assurance_fixtures import gates,repair_data
from apps.operator.assurance import Assurance,gate_projection,repair_projection
from apps.operator.service import Service
from apps.operator.contracts import Principal,PERMISSIONS
from bie.qa.release_v2.evaluator import ReleaseEvaluator
from bie.qa.release_v2.contracts import digest,EvidenceBundle
from bie.qa.repair_v2.journal import Journal

class AssuranceBase(ViewBase):
    def setUp(self):super().setUp();self.a=Assurance(self.service)
    def http(self,kind):return self.get('runs/'+self.run+'/assurance/'+kind)
    def setup_gate(self):self.evaluator,self.bundle,self.folder=gates(self.service,self.p,self.run,self.root)
    def publish_gate(self,as_of=1000):return self.a.bind_gates(self.p,self.run,self.evaluator,self.bundle,self.folder,as_of=as_of,evidence_origin='SYNTHETIC_TEST')

class Qa001(AssuranceBase):
    def test_canonical_release_evaluator_actually_invoked(self):
        self.setup_gate()
        with patch.object(ReleaseEvaluator,'evaluate',autospec=True,side_effect=lambda e,b,r,as_of:self.original(e,b,r,as_of=as_of)) as call:
            self.publish_gate()
        self.assertEqual(call.call_count,1)
    original=staticmethod(ReleaseEvaluator.evaluate)
    def test_all_28_policy_gates_shown_without_average(self):
        self.setup_gate();v=self.publish_gate()['view'];self.assertEqual(len(v['gates']),28);self.assertEqual(len(v['blocking_gates']),28)
    def test_missing_evidence_never_passes(self):
        self.setup_gate();v=self.publish_gate()['view'];self.assertTrue(all(g['status']=='PENDING' for g in v['gates']));self.assertEqual(v['native_release_status'],'BLOCKED')
    def test_no_candidate_has_truthful_not_run_policy_inventory(self):
        v=self.http('gates').json();self.assertEqual(v['status'],'NOT_RUN');self.assertEqual(len(v['required_gates']),28);self.assertTrue(all(g['status']=='NOT_RUN' for g in v['required_gates']))
    def test_posix_security_unsupported_not_bypassed(self):
        self.setup_gate();v=self.publish_gate()['view']
        if os.name=='nt':self.assertIn('SECURE_ARTIFACT_IO_UNSUPPORTED',v['global_reasons'])
        self.assertEqual(v['native_release_status'],'BLOCKED')
    def test_no_release_or_product_permission(self):
        self.setup_gate();v=self.publish_gate()['view'];self.assertFalse(v['product_accepted']);self.assertFalse(v['release_authorized']);self.assertFalse(v['current_deployment_authority'])
    def test_replay_and_restart_keep_same_native_report(self):
        self.setup_gate();v=self.publish_gate();self.assertEqual(v,self.publish_gate());self.assertEqual(v,Assurance(Service(self.root,self.creds)).get(self.p,self.run,'gates')['items'][0])
    def test_source_identity_exact(self):
        self.setup_gate();v=self.publish_gate()['view'];self.assertEqual(v['candidate_sha256'],self.body['source_hash']);self.assertEqual(v['native_candidate_digest'],self.bundle.candidate.content_digest)
    def test_arbitrary_json_evaluator_rejected(self):
        self.setup_gate();self.evaluator={};self.error(self.publish_gate,'native_gate_evaluator_required')
    def test_evaluator_subclass_is_not_a_native_port(self):
        self.setup_gate()
        class Fake(ReleaseEvaluator):pass
        self.evaluator=Fake();self.error(self.publish_gate,'native_gate_evaluator_required')
    def test_wrong_run_candidate_rejected(self):
        self.setup_gate();self.bundle=replace(self.bundle,candidate=replace(self.bundle.candidate,run_id='foreign'))
        self.error(self.publish_gate,'assurance_run_binding')
    def test_fixture_cannot_be_relabelled_native_producer(self):
        self.setup_gate();self.error(lambda:self.a.bind_gates(self.p,self.run,self.evaluator,self.bundle,self.folder,
            as_of=1000,evidence_origin='NATIVE_PRODUCER'),'assurance_fixture_promotion')
    def test_changed_candidate_content_rejected_before_evaluation(self):
        self.setup_gate();refs=self.bundle.candidate.artifacts;self.bundle=replace(self.bundle,candidate=replace(self.bundle.candidate,artifacts=(replace(refs[0],sha256='0'*64),)+refs[1:]))
        self.error(self.publish_gate,'assurance_candidate_binding')
    def test_cross_tenant_cannot_read_or_publish(self):
        self.setup_gate();self.publish_gate();self.error(lambda:self.a.get(self.foreign(),self.run,'gates'),'run_not_found')
    def test_read_permission_cannot_publish(self):
        self.setup_gate();p=Principal('reader','tenant-a',frozenset({'read'}),time.time()+100);self.creds.grant(secrets.token_hex(32),p)
        self.error(lambda:self.a.bind_gates(p,self.run,self.evaluator,self.bundle,self.folder,as_of=1000,evidence_origin='SYNTHETIC_TEST'),'forbidden')
    def test_expired_access_denied(self):
        self.creds.grant(self.token,Principal(self.p.actor,self.p.tenant,PERMISSIONS,time.time()-1));self.assertEqual(self.http('gates').status_code,401)
    def test_revoked_access_denied(self):self.creds.revoke(self.token);self.assertEqual(self.http('gates').status_code,401)
    def test_persisted_gate_blob_tamper_rejected(self):
        self.setup_gate();v=self.publish_gate();self.tamper_blob(v['artifact_id']);self.assertEqual(self.http('gates').status_code,500)
    def test_video_parent_tamper_rejected_on_read(self):
        self.setup_gate();self.publish_gate();self.tamper_blob('fixture-video');self.assertEqual(self.http('gates').status_code,500)
    def test_game_parent_tamper_rejected_on_read(self):
        self.setup_gate();self.publish_gate();self.tamper_blob('fixture-game');self.assertEqual(self.http('gates').status_code,500)
    def test_blocking_inventory_tamper_rejected(self):
        self.setup_gate();r=self.original(self.evaluator,self.bundle,self.folder,as_of=1000)
        self.error(lambda:gate_projection(replace(r,blocking_gates=()),self.bundle,self.evaluator.policy),'gate_blockers_invalid')
    def test_duplicate_gate_rejected(self):
        self.setup_gate();r=self.original(self.evaluator,self.bundle,self.folder,as_of=1000)
        self.error(lambda:gate_projection(replace(r,gate_results=(r.gate_results[0],)*28),self.bundle,self.evaluator.policy),'gate_inventory_invalid')
    def test_gate_ownership_not_reassigned(self):
        self.setup_gate();r=self.original(self.evaluator,self.bundle,self.folder,as_of=1000)
        self.error(lambda:gate_projection(replace(r,gate_results=(replace(r.gate_results[0],owner='FAKE'),)+r.gate_results[1:]),self.bundle,self.evaluator.policy),'gate_status_invalid')
    def test_readonly_http_no_gate_success_publisher(self):self.assertEqual(self.post('runs/'+self.run+'/assurance/gates',{'status':'PASS'}).status_code,405)
    def test_unknown_kind_not_fixture_fallback(self):self.assertEqual(self.http('unknown').status_code,404)
    def test_safe_output_no_paths_credentials_or_raw_candidate(self):
        self.setup_gate();self.publish_gate();r=self.http('gates');self.assertEqual(r.status_code,200)
        for s in (str(self.folder),str(self.root),self.token,'Authored non-media','source.bin'):self.assertNotIn(s,r.text)
        self.assertNotIn('access-control-allow-origin',r.headers);self.assertEqual(r.headers['cache-control'],'no-store')
    def test_bounded_snapshot_pagination(self):
        self.setup_gate();self.publish_gate(1000);self.publish_gate(1001);v=self.a.get(self.p,self.run,'gates',0,1)
        self.assertEqual(v['total'],2);self.assertEqual(v['next_offset'],1)
        self.error(lambda:self.a.get(self.p,self.run,'gates',0,101),'invalid_pagination')
    def test_interrupted_binding_replays_without_duplicate(self):
        self.setup_gate()
        with patch.object(self.service.catalog,'event',side_effect=RuntimeError('seeded_failure')):
            with self.assertRaises(RuntimeError):self.publish_gate()
        self.publish_gate();self.assertEqual(self.a.get(self.p,self.run,'gates')['total'],1)

class Qa003Projection(AssuranceBase):
    def data(self,status='REJECTED'):self.parts=repair_data(self.body,self.ref,status);return self.parts
    def project(self):return repair_projection(*self.parts)
    def test_native_journal_unbound_not_fake_history(self):
        v=self.http('repairs').json();self.assertEqual(v['status'],'NOT_RUN');self.assertEqual(v['items'],[])
    def test_dictionary_never_accepted_as_native_journal(self):
        self.error(lambda:self.a.bind_repairs(self.p,self.run,{},None,(),evidence_origin='SYNTHETIC_TEST'),'native_repair_journal_required')
    def test_unit_pending_reservation_is_manual_review(self):
        self.data('PENDING');a=self.project()['attempts'][0];self.assertEqual(a['status'],'REVIEW_REQUIRED');self.assertFalse(a['worker_executed'])
    def test_unit_rejected_attempt_retains_diagnostics(self):
        self.data();v=self.project();self.assertEqual(v['attempts'][0]['status'],'REJECTED');self.assertTrue(v['attempts'][0]['diagnostics'])
    def test_unit_staged_is_review_not_release(self):
        self.data('STAGED_FOR_REVIEW');v=self.project();self.assertEqual(v['attempts'][0]['status'],'STAGED_FOR_REVIEW');self.assertFalse(v['release_authorized'])
    def test_unit_staged_requires_authenticated_inventory(self):
        self.data('STAGED_FOR_REVIEW');self.parts=self.parts[:1]+(replace(self.parts[1],authenticated=False),)+self.parts[2:]
        r=self.parts[-1][0];r['plan_digest']=self.parts[1].content_digest
        r['receipt_digest']=digest({k:v for k,v in r.items() if k not in ('receipt_digest','journal_head')})
        self.parts[0]['events'][-1]['receipt_digest']=r['receipt_digest']
        self.error(self.project,'repair_staged_without_checks')
    def test_unit_before_after_and_regression_visible(self):
        self.data('STAGED_FOR_REVIEW');v=self.project();self.assertNotEqual(v['snapshot_digest'],v['attempts'][0]['candidate_digest']);self.assertEqual(v['attempts'][0]['checks'][0]['status'],'PASS')
    def test_unit_no_paths_raw_receipt_or_worker_message_leak(self):
        self.data('STAGED_FOR_REVIEW');raw=json.dumps(self.project());self.assertNotIn('PRIVATE_PATH',raw);self.assertNotIn('staged_directory',raw);self.assertNotIn('promotion_requires',raw)
    def test_unit_remaining_defects_and_owner_retained(self):
        self.data();v=self.project();self.assertEqual(v['defects'][0]['owner'],'BI');self.assertEqual(v['attempts'][0]['remaining_failure_ids'],['failure-one'])
    def test_unit_receipt_tamper_rejected(self):
        self.data();self.parts[-1][0]['status']='STAGED_FOR_REVIEW';self.error(self.project,'repair_receipt_integrity')
    def test_unit_missing_finished_receipt_rejected(self):
        self.data();self.parts=self.parts[:-1]+((),);self.error(self.project,'repair_receipt_inventory')
    def test_unit_duplicate_attempt_receipt_rejected(self):
        self.data();self.parts=self.parts[:-1]+(self.parts[-1]*2,);self.error(self.project,'repair_duplicate_receipt')
    def test_unit_journal_binding_change_rejected(self):
        self.data();self.parts[0]['binding']['run_id']='other';self.error(self.project,'repair_context_binding')
    def test_unit_product_promotion_rejected(self):
        self.data();self.parts[0]['product_accepted']=True;self.error(self.project,'repair_unauthorized_promotion')
    def test_unit_event_transition_rejected(self):
        self.data();self.parts[0]['events'].reverse();self.error(self.project,'repair_journal_event_invalid')
    def test_unit_boolean_attempt_not_integer(self):
        self.data();self.parts[-1][0]['attempt']=True;self.error(self.project,'quality_count_invalid')
    def test_unit_context_policy_change_rejected(self):
        self.data();self.parts=self.parts[:1]+(replace(self.parts[1],policy_digest='0'*64),)+self.parts[2:];self.error(self.project,'repair_context_binding')
    def test_unit_repeated_projection_deterministic(self):self.data();self.assertEqual(self.project(),self.project())
    def test_no_http_repair_executor_or_receipt_publisher(self):self.assertEqual(self.post('runs/'+self.run+'/assurance/repairs',{'status':'STAGED_FOR_REVIEW'}).status_code,405)
    def test_missing_journal_cannot_mark_repaired(self):self.assertNotIn('REPAIRED',self.http('repairs').text)
    def test_native_journal_guard_not_monkeypatched_on_windows(self):
        self.assertEqual(Journal.__module__,'bie.qa.repair_v2.journal')
        if os.name=='nt':self.assertFalse(hasattr(os,'O_NOFOLLOW'))

TASK_CLASSES={'BIE-APP-QA-001':Qa001,'BIE-APP-QA-003':Qa003Projection}
def selected_suite(task=None):
    suite=unittest.TestSuite()
    for key,cls in TASK_CLASSES.items():
        if task is None or task==key:
            for m in sorted(cls.__dict__):
                if m.startswith('test_'):suite.addTest(cls(m))
    return suite
if __name__=='__main__':unittest.TextTestRunner(verbosity=2).run(selected_suite())
