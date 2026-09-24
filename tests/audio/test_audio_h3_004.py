import time,threading,json
from unittest.mock import patch
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from bie.audio.durable_pipeline import *
from bie.director.director_durable_recovery import RecoveryError
from bie.audio.acoustic_contract import BOUNDARIES,SCOPE
from bie.audio.durable_contract import DurablePolicy
from bie.audio.qa_contract import require_qa_pass
from .durable_test_support import *
from .acoustic_test_support import sign_test_payload

class DurablePipelineTests(DurableCase):
    def setUp(self):
        super().setUp();now=int(time.time())
        self.live_trust=clone(self.trust)
        self.live_trust['issuers'][0]['not_before']=now-60
        self.live_trust['issuers'][0]['not_after']=now+86400
    def options(self,**kw):
        return dict(root=self.root/'service',run_id=RUN_ID,job_id='scene-1',revision=kw.pop('revision','1'),
            runtime=self.runtime,trust=self.live_trust,signer=self.signer,key_id=KEY_ID,**kw)
    def fixed_measured_receipt(self,*args,**kw):
        now=int(time.time())
        return sign_test_payload({'schema_version':'bie.audio.evaluator-payload/1','key_id':KEY_ID,
            'scope':SCOPE,'issued_at':now,'expires_at':now+600,'job_fingerprint':self.job['fingerprint'],
            'binding':clone(self.job['binding']),'measurement':clone(self.measurement),**BOUNDARIES},self.signer)
    def test_actual_native_evaluation_and_cold_reuse(self):
        # Actual unpatched waveform evaluation. Short lease exercises heartbeats
        # on the local recognizer; no live voice or acceptance claim.
        opts=self.options(durable_policy=DurablePolicy(lease_ttl_seconds=3,heartbeat_seconds=1))
        first=evaluate_durable(self.mix,self.sync,**opts)
        self.assertEqual(first['native_evaluations'],1);self.assertFalse(first['cache_hit'])
        with patch('bie.audio.durable_pipeline.issue_evaluation',side_effect=AssertionError('native must not rerun')):
            second=evaluate_durable(self.mix,self.sync,**opts)
        self.assertEqual(first['artifact_ref'],second['artifact_ref']);self.assertTrue(second['signature_reverified'])
        self.assertEqual(second['native_evaluations'],0)
    def test_qa_adopts_actual_signed_result(self):
        with patch('bie.audio.durable_pipeline.issue_evaluation',side_effect=self.fixed_measured_receipt):
            result,report,captions=audit_durable_mix(self.mix,self.sync,**self.options())
        self.assertEqual(report['binding']['acoustic_receipt_fingerprint'],fingerprint(result['receipt']))
        self.assertEqual(report['status'],'REVIEW');self.assertEqual(len(report['checks']),5)
    def test_still_not_release_authority(self):
        with patch('bie.audio.durable_pipeline.issue_evaluation',side_effect=self.fixed_measured_receipt):
            result,report,captions=audit_durable_mix(self.mix,self.sync,**self.options())
        with self.assertRaises(AudioError):require_qa_pass(report)
    def test_original_upstream_review_findings_survive(self):
        with patch('bie.audio.durable_pipeline.issue_evaluation',side_effect=self.fixed_measured_receipt):
            result,report,_=audit_durable_mix(self.mix,self.sync,**self.options())
        codes={f['code'] for c in report['checks'] for f in c['findings']}
        self.assertTrue({'INDEPENDENT_PRONUNCIATION_UNVERIFIED','ACTUAL_RENDERED_AV_SYNC_UNVERIFIED'}<=codes)
    def test_signer_rejected_before_worker(self):
        opts=self.options();opts['signer']=Ed25519PrivateKey.generate()
        with patch('bie.audio.durable_pipeline.issue_evaluation') as issue:
            with self.assertRaisesRegex(AudioError,'SIGNER'):evaluate_durable(self.mix,self.sync,**opts)
            issue.assert_not_called()
    def test_revoked_signer_rejected_before_worker(self):
        self.live_trust['issuers'][0]['revoked']=True
        with self.assertRaises(AudioError):evaluate_durable(self.mix,self.sync,**self.options())
    def test_runtime_drift_rejected(self):
        opts=self.options();r=clone(self.runtime);r['files']['dictionary']['sha256']='0'*64;rehash(r);opts['runtime']=r
        with self.assertRaises(AudioError):evaluate_durable(self.mix,self.sync,**opts)
    def test_cancel_before_storage(self):
        cancel=threading.Event();cancel.set()
        with self.assertRaisesRegex(AudioError,'CANCELLED'):evaluate_durable(self.mix,self.sync,**self.options(cancellation=cancel))
        self.assertFalse((self.root/'service').exists())
    def test_cancel_running_work_leaves_no_completed_receipt(self):
        cancel=threading.Event()
        def until_cancel(*args,**kw):
            kw['cancellation'].wait(5);raise AudioError('ACOUSTIC_CANCELLED')
        timer=threading.Timer(.5,cancel.set);timer.start()
        try:
            with patch('bie.audio.durable_pipeline.issue_evaluation',side_effect=until_cancel):
                with self.assertRaisesRegex(AudioError,'CANCELLED'):evaluate_durable(self.mix,self.sync,**self.options(cancellation=cancel))
        finally:timer.cancel()
        with AudioJobCoordinator(self.root/'service/jobs').session() as (leases,claims):
            self.assertEqual(claims.db.execute('SELECT state FROM claims').fetchone()[0],'CLAIMED')
    def test_worker_failure_not_cached_as_success(self):
        with patch('bie.audio.durable_pipeline.issue_evaluation',side_effect=AudioError('ACOUSTIC_WORKER_FAILED')):
            with self.assertRaises(AudioError):evaluate_durable(self.mix,self.sync,**self.options())
        with self.assertRaises(RuntimeError):evaluate_durable(self.mix,self.sync,**self.options())
    def test_new_revision_explicitly_runs_again(self):
        with patch('bie.audio.durable_pipeline.issue_evaluation',side_effect=self.fixed_measured_receipt) as issue:
            a=evaluate_durable(self.mix,self.sync,**self.options());b=evaluate_durable(self.mix,self.sync,**self.options(revision='2'))
        self.assertEqual(issue.call_count,2);self.assertNotEqual(a['artifact_ref'],b['artifact_ref'])
    def test_trust_revision_reverified_without_rerun(self):
        with patch('bie.audio.durable_pipeline.issue_evaluation',side_effect=self.fixed_measured_receipt) as issue:
            a=evaluate_durable(self.mix,self.sync,**self.options());self.live_trust['revision']='TEST_ONLY_NEW'
            b=evaluate_durable(self.mix,self.sync,**self.options())
        self.assertEqual(issue.call_count,1);self.assertEqual(b['assessment']['trust_fingerprint'],fingerprint(self.live_trust))
    def test_same_revision_changed_key_refuses_alias(self):
        with patch('bie.audio.durable_pipeline.issue_evaluation',side_effect=self.fixed_measured_receipt):evaluate_durable(self.mix,self.sync,**self.options())
        self.live_trust['issuers'][0]['key_id']='new-id';opts=self.options();opts['key_id']='new-id'
        with self.assertRaises(RecoveryError):evaluate_durable(self.mix,self.sync,**opts)
    def test_current_evidence_publication_connected(self):
        dest=self.root/'out'
        with patch('bie.audio.durable_pipeline.issue_evaluation',side_effect=self.fixed_measured_receipt):
            result,report,captions=audit_durable_mix(self.mix,self.sync,output=dest,**self.options())
        self.assertTrue(verify_publication(dest,self.mix,self.sync,self.live_trust)['passed'])
    def test_native_worker_boundary_label_honest(self):
        with patch('bie.audio.durable_pipeline.issue_evaluation',side_effect=self.fixed_measured_receipt):r=evaluate_durable(self.mix,self.sync,**self.options())
        self.assertEqual(r['native_worker_scope'],'H2_BOUNDED_LOCAL_NOT_CANONICAL_KERNEL')
        self.assertFalse(r['product_accepted'])
