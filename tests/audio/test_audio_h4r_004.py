"""H4-R1-004 actual CAS/SQLite/FencedLease integration; no replacement stores."""
from pathlib import Path
from threading import Event
from unittest.mock import patch
import json
import tempfile
import unittest
from bie.audio.common import AudioError,fingerprint
from bie.director.director_durable_recovery import RecoveryError
from bie.audio.acoustic_contract import canonical
from bie.audio.durable_contract import DurablePolicy,build_request
from bie.audio.durable_jobs import AudioJobCoordinator
from bie.audio.kernel_durable import KernelArtifactStore,build_kernel_request,kernel_policy,complete_kernel
from . import kernel_test_support as k

class DurableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.c=k.context();cls.r=k.actual_receipt()
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.store=KernelArtifactStore(self.root/'artifacts',runtime=self.c['runtime'],profile=self.c['profile'])
        self.jobs=AudioJobCoordinator(self.root/'jobs',policy=self.store.policy)
        self.request=k.clone(self.c['request'])
    def put(self):return self.store.put(self.request,self.c['mixed'].wav_bytes,self.r,self.c['trust'])
    def test_canonical_four_envelopes(self):
        ref=self.put();loaded=self.store.load(ref,self.request,self.c['trust'])
        self.assertTrue(loaded['kernel_signature_reverified']);self.assertTrue(loaded['signature_reverified'])
        self.assertEqual(ref['artifact_type'],'audio.acoustic.kernel-evaluation')
        self.assertEqual(loaded['receipt'],self.r['payload']['compatibility_receipt'])
        with self.store.base.session() as io:
            outer=io.load(__import__('bie.director.director_artifacts',fromlist=['reference']).reference(ref))
            self.assertEqual(len(outer.parent_refs),1)
    def test_signed_durable_request(self):
        self.assertEqual(self.r['payload']['durable_request_fingerprint'],self.request['fingerprint'])
    def test_idempotent_artifact_put(self):self.assertEqual(self.put(),self.put())
    def test_legacy_envelope_rejected(self):
        ref=self.store.base.put(self.request,self.c['mixed'].wav_bytes,
            self.r['payload']['compatibility_receipt'],self.c['trust']['evaluator_trust'])
        with self.assertRaises(AudioError):self.store.load(ref,self.request,self.c['trust'])
    def test_legacy_request_policy_rejected(self):
        old=build_request(self.c['job'],run_id=k.RUN_ID,job_id='synthetic-kernel-fixture',
            revision='H4R1-r1',runtime_fingerprint=self.c['runtime']['fingerprint'],key_id=k.KEY_ID)
        with self.assertRaises(AudioError):self.store.put(old,self.c['mixed'].wav_bytes,self.r,self.c['trust'])
    def test_new_revision_requires_new_signature(self):
        req=build_kernel_request(self.c['job'],profile=self.c['profile'],runtime=self.c['runtime'],
            run_id=k.RUN_ID,job_id='other',revision='H4R1-r1',key_id=k.KEY_ID)
        with self.assertRaises(AudioError):self.store.put(req,self.c['mixed'].wav_bytes,self.r,self.c['trust'])
    def test_receipt_revocation_rechecked_on_load(self):
        ref=self.put();trust=k.clone(self.c['trust']);trust['evaluator_trust']['issuers'][0]['revoked']=True
        with self.assertRaises(AudioError):self.store.load(ref,self.request,trust)
    def test_profile_approval_rechecked(self):
        ref=self.put();trust=k.clone(self.c['trust']);trust['profile_fingerprints']=['sha256:'+'0'*64]
        with self.assertRaises(AudioError):self.store.load(ref,self.request,trust)
    def test_expired_stored_receipt(self):
        ref=self.put()
        with self.assertRaises(AudioError):self.store.load(ref,self.request,self.c['trust'],now=self.r['payload']['expires_at'])
    def test_corrupt_cas_media(self):
        ref=self.put();h=self.r['payload']['execution']['media_sha256']
        p=self.store.base.root/'cas/blobs/sha256'/h[:2]/h;p.write_bytes(b'tampered')
        with self.assertRaises((AudioError,ValueError)):self.store.load(ref,self.request,self.c['trust'])
    def test_active_fence_completes(self):
        ticket=self.jobs.acquire(self.request);ref=self.put()
        loaded=complete_kernel(self.jobs,ticket,canonical(ref).decode(),self.store,self.request,self.c['trust'])
        self.assertTrue(loaded['kernel_signature_reverified']);self.assertEqual(self.jobs.state(self.request)['lease_state'],'COMPLETED')
    def test_expired_fence_blocked(self):
        issued=self.r['payload']['issued_at'];ticket=self.jobs.acquire(self.request,now=issued)
        ref=self.put()
        with self.assertRaises(RecoveryError):
            complete_kernel(self.jobs,ticket,canonical(ref).decode(),self.store,self.request,self.c['trust'],now=issued+31)
        self.assertNotEqual(self.jobs.state(self.request)['lease_state'],'COMPLETED')
    def test_claim_complete_crash_recovered(self):
        issued=self.r['payload']['issued_at'];ticket=self.jobs.acquire(self.request,now=issued);ref=self.put();encoded=canonical(ref).decode()
        with self.jobs.session() as (_,claims):claims.complete(ticket.lease.key,ticket.lease.owner,encoded)
        new=self.jobs.acquire(self.request,now=issued+31)
        self.assertEqual(new.claimed_result_ref,encoded)
        complete_kernel(self.jobs,new,encoded,self.store,self.request,self.c['trust'],now=issued+31)
        self.assertEqual(self.jobs.state(self.request)['claim_state'],'COMPLETED')
    def test_stale_owner_cannot_complete(self):
        issued=self.r['payload']['issued_at'];old=self.jobs.acquire(self.request,now=issued);ref=self.put()
        new=self.jobs.acquire(self.request,now=issued+31);self.assertNotEqual(old.lease.owner,new.lease.owner)
        with self.assertRaises(RecoveryError):
            complete_kernel(self.jobs,old,canonical(ref).decode(),self.store,self.request,self.c['trust'],now=issued+31)
    def test_precancel_creates_no_durable_root(self):
        e=Event();e.set();root=self.root/'cancel-store'
        with self.assertRaises(AudioError):k.pipeline(root,cancellation=e)
        self.assertFalse(root.exists())
    def test_native_failure_never_marks_completed(self):
        with patch('bie.audio.kernel_durable.issue_kernel_evaluation',side_effect=AudioError('INJECTED_NATIVE_FAILURE')):
            with self.assertRaises(AudioError):k.pipeline(self.root/'pipeline')
        jobs=AudioJobCoordinator(self.root/'pipeline/jobs',policy=self.store.policy)
        self.assertNotEqual(jobs.state(self.request)['claim_state'],'COMPLETED')
    def test_actual_cold_then_zero_native_reuse(self):
        cold=k.pipeline(self.root/'pipeline')
        with patch('bie.audio.kernel_durable.issue_kernel_evaluation',side_effect=AssertionError('must not call native')):
            warm=k.pipeline(self.root/'pipeline')
        self.assertFalse(cold['cache_hit']);self.assertTrue(warm['cache_hit'])
        self.assertEqual(warm['native_evaluations'],0);self.assertEqual(cold['artifact_ref'],warm['artifact_ref'])
    def test_direct_legacy_receipt_cannot_be_put(self):
        with self.assertRaises(AudioError):self.store.put(self.request,self.c['mixed'].wav_bytes,
            self.r['payload']['compatibility_receipt'],self.c['trust'])
