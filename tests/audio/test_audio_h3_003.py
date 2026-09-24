import json,sqlite3,time,threading
from dataclasses import replace
from bie.director.director_durable_recovery import DirectorLeaseStore,RecoveryError
from bie.audio.common import AudioError
from bie.audio.durable_contract import *
from bie.audio.durable_jobs import *
from .durable_test_support import *

class FencedLifecycleTests(DurableCase):
    def test_live_job_cannot_be_stolen(self):
        self.jobs.acquire(self.request,now=NOW)
        with self.assertRaises(RecoveryError):self.jobs.acquire(self.request,now=NOW+1)
    def test_new_invocation_has_unique_owner(self):
        a=self.jobs.acquire(self.request,now=NOW);b=self.jobs.acquire(self.request,now=NOW+31)
        self.assertNotEqual(a.lease.owner,b.lease.owner);self.assertEqual(b.lease.epoch,2)
    def test_expired_claim_reclaimed(self):
        self.jobs.acquire(self.request,now=NOW);t=self.jobs.acquire(self.request,now=NOW+31)
        with self.jobs.session() as (_,claims):self.assertEqual(claims.get(t.lease.key).owner,t.lease.owner)
    def test_old_worker_cannot_complete(self):
        old=self.jobs.acquire(self.request,now=NOW);self.jobs.acquire(self.request,now=NOW+31);ref=self.put()
        with self.assertRaises(RecoveryError):self.jobs.complete(old,canonical(ref).decode(),self.store,self.request,self.trust,now=NOW+32)
    def test_heartbeat_extends_live_lease(self):
        t=self.jobs.acquire(self.request,now=NOW);h=self.jobs.heartbeat(t,now=NOW+20)
        self.assertEqual(h.lease.expires_at,NOW+50)
        with self.assertRaises(RecoveryError):self.jobs.acquire(self.request,now=NOW+35)
    def test_old_heartbeat_ticket_cannot_complete(self):
        t=self.jobs.acquire(self.request,now=NOW);self.jobs.heartbeat(t,now=NOW+20);ref=self.put()
        with self.assertRaises(RecoveryError):self.jobs.complete(t,canonical(ref).decode(),self.store,self.request,self.trust,now=NOW+21)
    def test_expired_heartbeat_fails(self):
        t=self.jobs.acquire(self.request,now=NOW)
        with self.assertRaises(RecoveryError):self.jobs.heartbeat(t,now=NOW+31)
    def test_completion_has_actual_verified_reference(self):
        t,ref=self.complete();state=self.jobs.state(self.request)
        self.assertEqual(state['lease_state'],'COMPLETED');self.assertEqual(state['claim_state'],'COMPLETED');self.assertEqual(json.loads(state['result_ref']),ref)
    def test_completed_claim_reused_after_restart(self):
        self.complete();other=AudioJobCoordinator(self.root/'jobs');t=other.acquire(self.request,now=NOW+10)
        self.assertIsNotNone(t.claimed_result_ref);self.assertEqual(t.lease.epoch,1)
    def test_crash_between_two_completion_markers_recovers(self):
        t=self.jobs.acquire(self.request,now=NOW);ref=self.put();encoded=canonical(ref).decode()
        with self.jobs.session() as (_,claims):claims.complete(t.lease.key,t.lease.owner,encoded)
        recovered=self.jobs.acquire(self.request,now=NOW+31)
        self.assertEqual(recovered.claimed_result_ref,encoded)
        self.jobs.complete(recovered,encoded,self.store,self.request,self.trust,now=NOW+32)
        self.assertEqual(self.jobs.state(self.request)['lease_state'],'COMPLETED')
    def test_recovery_still_rechecks_signature(self):
        t=self.jobs.acquire(self.request,now=NOW);ref=self.put();encoded=canonical(ref).decode()
        with self.jobs.session() as (_,claims):claims.complete(t.lease.key,t.lease.owner,encoded)
        recovered=self.jobs.acquire(self.request,now=NOW+601)
        with self.assertRaises(AudioError):self.jobs.complete(recovered,encoded,self.store,self.request,self.trust,now=NOW+601)
        self.assertEqual(self.jobs.state(self.request)['lease_state'],'ACTIVE')
    def test_attempt_limit(self):
        self.jobs.acquire(self.request,now=NOW);self.jobs.acquire(self.request,now=NOW+31);self.jobs.acquire(self.request,now=NOW+62)
        with self.assertRaisesRegex(AudioError,'ATTEMPTS'):self.jobs.acquire(self.request,now=NOW+93)
    def test_changed_same_revision_conflict(self):
        self.jobs.acquire(self.request,now=NOW);r=clone(self.request);r['key_id']='other';rehash(r)
        with self.assertRaises(RecoveryError):self.jobs.acquire(r,now=NOW+31)
    def test_new_revision_can_run(self):
        self.jobs.acquire(self.request,now=NOW);r=build_request(self.job,run_id=RUN_ID,job_id='scene-1',revision='2',runtime_fingerprint=self.runtime['fingerprint'],key_id=KEY_ID)
        self.assertEqual(self.jobs.acquire(r,now=NOW).lease.epoch,1)
    def test_fake_callback_cannot_authorize_completion(self):
        t=self.jobs.acquire(self.request,now=NOW)
        with self.assertRaisesRegex(AudioError,'STORE_REQUIRED'):self.jobs.complete(t,'{}',lambda:True,self.request,self.trust,now=NOW)
    def test_wrong_ticket_request(self):
        t=self.jobs.acquire(self.request,now=NOW);r=build_request(self.job,run_id=RUN_ID,job_id='other',revision='1',runtime_fingerprint=self.runtime['fingerprint'],key_id=KEY_ID)
        with self.assertRaisesRegex(AudioError,'TICKET'):self.jobs.complete(t,'{}',self.store,r,self.trust,now=NOW)
    def test_concurrent_process_connections_only_one_claims(self):
        successes=[];errors=[];barrier=threading.Barrier(3)
        def work():
            barrier.wait()
            try:successes.append(AudioJobCoordinator(self.root/'jobs').acquire(self.request,now=NOW))
            except RecoveryError as exc:errors.append(exc)
        threads=[threading.Thread(target=work) for _ in range(2)]
        for t in threads:t.start()
        barrier.wait()
        for t in threads:t.join()
        self.assertEqual(len(successes),1);self.assertEqual(len(errors),1)
    def test_stale_result_reference_cannot_complete(self):
        t=self.jobs.acquire(self.request,now=NOW);ref=self.put();ref['content_hash']='0'*64
        with self.assertRaises(ValueError):self.jobs.complete(t,canonical(ref).decode(),self.store,self.request,self.trust,now=NOW)
        self.assertEqual(self.jobs.state(self.request)['claim_state'],'CLAIMED')

    def test_exact_expiry_cannot_heartbeat_or_complete(self):
        t=self.jobs.acquire(self.request,now=NOW);ref=self.put()
        with self.assertRaisesRegex(AudioError,'EXPIRED'):self.jobs.heartbeat(t,now=NOW+30)
        with self.assertRaisesRegex(AudioError,'EXPIRED'):self.jobs.complete(t,canonical(ref).decode(),self.store,self.request,self.trust,now=NOW+30)
