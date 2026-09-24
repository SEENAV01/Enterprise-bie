import unittest,tempfile
from pathlib import Path
from bie.audio.neural_call_journal import PaidCallJournal,CallTicket
from bie.audio.common import AudioError,fingerprint
from bie.audio.tts_contract import ProviderFailure

REQ=fingerprint('request');DEP=fingerprint('deployment');PAY='a'*64

class H8PaidCallJournalTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.j=PaidCallJournal(Path(self.tmp.name)/'journal')
    def prep(self):return self.j.prepare(request_fingerprint=REQ,deployment_fingerprint=DEP,payload_sha256=PAY)
    def test_new_call_is_prepared(self):
        t=self.prep();s=self.j.safe_state(t.call_key);self.assertEqual(s['state'],'PREPARED');self.assertEqual(s['attempt_no'],1)
    def test_prepared_is_reused_before_send(self):
        a=self.prep();b=self.prep();self.assertEqual(a,b)
    def test_mark_inflight(self):
        t=self.prep();self.j.mark_in_flight(t);self.assertEqual(self.j.safe_state(t.call_key)['state'],'IN_FLIGHT')
    def test_restart_inflight_becomes_uncertain_and_blocks(self):
        t=self.prep();self.j.mark_in_flight(t)
        with self.assertRaisesRegex(ProviderFailure,'UNCERTAIN_REMOTE_COMPLETION'):self.prep()
        self.assertEqual(self.j.safe_state(t.call_key)['state'],'UNCERTAIN')
    def test_uncertain_requires_resolution(self):
        t=self.prep();self.j.mark_in_flight(t);self.j.mark_uncertain(t)
        with self.assertRaisesRegex(ProviderFailure,'REISSUE_REQUIRES_RESOLUTION'):self.prep()
    def test_rejected_requires_resolution(self):
        t=self.prep();self.j.mark_in_flight(t);self.j.mark_rejected(t,http_status=429)
        with self.assertRaisesRegex(ProviderFailure,'REISSUE_REQUIRES_RESOLUTION'):self.prep()
    def test_resolution_creates_new_attempt(self):
        t=self.prep();self.j.mark_in_flight(t);self.j.mark_uncertain(t);self.j.authorize_reissue(t.call_key,resolution_ref='provider:audit:001',authority_revision='ops-r2')
        n=self.prep();self.assertEqual(n.attempt_no,2);self.assertNotEqual(n.attempt_id,t.attempt_id);self.assertEqual(self.j.safe_state(t.call_key)['state'],'PREPARED')
    def test_resolution_only_for_uncertain_or_rejected(self):
        t=self.prep()
        with self.assertRaisesRegex(AudioError,'RESOLUTION_STATE'):self.j.authorize_reissue(t.call_key,resolution_ref='x',authority_revision='r')
    def test_confirmed_blocks_resynthesis_without_cache(self):
        t=self.prep();self.j.mark_in_flight(t);self.j.mark_confirmed(t,provider_request_id='req-1',response_sha256='b'*64)
        with self.assertRaisesRegex(ProviderFailure,'CONFIRMED_REMOTE_RESPONSE'):self.prep()
    def test_cached_response_can_reconcile_missing_journal(self):
        key=self.j.reconcile_cached(request_fingerprint=REQ,deployment_fingerprint=DEP,payload_sha256=PAY,provider_request_id='req-1',response_sha256='b'*64)
        self.assertEqual(self.j.safe_state(key)['state'],'CONFIRMED')
    def test_cached_response_can_reconcile_uncertain(self):
        t=self.prep();self.j.mark_in_flight(t);self.j.mark_uncertain(t)
        self.j.reconcile_cached(request_fingerprint=REQ,deployment_fingerprint=DEP,payload_sha256=PAY,provider_request_id='req-1',response_sha256='b'*64)
        self.assertEqual(self.j.safe_state(t.call_key)['state'],'CONFIRMED')
    def test_conflicting_cached_response_is_rejected(self):
        t=self.prep();self.j.mark_in_flight(t);self.j.mark_confirmed(t,provider_request_id='req-1',response_sha256='b'*64)
        with self.assertRaisesRegex(AudioError,'CACHE_CONFLICT'):self.j.reconcile_cached(request_fingerprint=REQ,deployment_fingerprint=DEP,payload_sha256=PAY,provider_request_id='req-2',response_sha256='c'*64)
    def test_stale_ticket_rejected(self):
        t=self.prep();bad=CallTicket(t.call_key,'call-deadbeef',t.attempt_no,PAY)
        with self.assertRaisesRegex(AudioError,'TICKET_STALE'):self.j.mark_in_flight(bad)
    def test_safe_state_contains_no_payload_or_secret(self):
        t=self.prep();state=self.j.safe_state(t.call_key);self.assertNotIn('payload_sha256',state);self.assertNotIn(PAY,repr(state));self.assertNotIn('secret',repr(state).lower())
    def test_safe_states_are_deterministic_order(self):
        other='c'*64;self.j.prepare(request_fingerprint=fingerprint('r2'),deployment_fingerprint=DEP,payload_sha256=other)
        self.prep();rows=self.j.safe_states();self.assertEqual([r['call_key'] for r in rows],sorted(r['call_key'] for r in rows))
    def test_identity_conflict_cannot_alias(self):
        key=PaidCallJournal.call_key(REQ,DEP,PAY);self.assertTrue(key.startswith('sha256:'))
        self.assertNotEqual(key,PaidCallJournal.call_key(fingerprint('other'),DEP,PAY))

if __name__=='__main__':unittest.main()
