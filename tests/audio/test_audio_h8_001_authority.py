import unittest
from bie.audio.neural_authority import LiveProviderPolicy,LiveProviderAuthority,EnvironmentSecretAuthority
from bie.audio.common import AudioError
from bie.audio.tts_contract import ProviderFailure
from tests.audio.neural_test_support import setup,config
import tempfile
from pathlib import Path

class H8AuthorityTests(unittest.TestCase):
    def policy(self,**kw):
        base=dict(authority_revision='ops-rev-2026-09-24',egress_approved=True,max_session_calls=4,max_session_chars=1000,max_inflight=2)
        base.update(kw);return LiveProviderPolicy(**base)
    def test_exact_origin_is_fixed(self):
        with self.assertRaisesRegex(AudioError,'ORIGIN'):LiveProviderPolicy('r',True,api_origin='https://evil.example')
    def test_provider_is_fixed(self):
        with self.assertRaisesRegex(AudioError,'ORIGIN'):LiveProviderPolicy('r',True,provider_id='other')
    def test_credential_binding_format(self):
        with self.assertRaisesRegex(AudioError,'BINDING'):LiveProviderPolicy('r',True,credential_env='bad-name')
    def test_egress_must_be_approved(self):
        a=LiveProviderAuthority(self.policy(egress_approved=False),environment={'ELEVENLABS_API_KEY':'fixture_secret_123'})
        with self.assertRaisesRegex(ProviderFailure,'EGRESS'):a.authorize('GET','/v1/models')
    def test_missing_secret_fails_closed(self):
        a=LiveProviderAuthority(self.policy(),environment={})
        with self.assertRaisesRegex(ProviderFailure,'CREDENTIALS'):a.authorize('GET','/v1/models')
    def test_secret_is_resolved_at_call_time_rotation(self):
        env={'ELEVENLABS_API_KEY':'first_secret_123'};a=LiveProviderAuthority(self.policy(),environment=env)
        self.assertEqual(a.authorize('GET','/v1/models'),'first_secret_123')
        env['ELEVENLABS_API_KEY']='second_secret_456'
        self.assertEqual(a.authorize('GET','/v1/models'),'second_secret_456')
    def test_receipt_never_contains_secret(self):
        secret='fixture_secret_123';a=LiveProviderAuthority(self.policy(),environment={'ELEVENLABS_API_KEY':secret})
        a.authorize('GET','/v1/models');r=repr(a)+repr(a.receipt())
        self.assertNotIn(secret,r);self.assertIn('<redacted>',repr(a));self.assertFalse(a.receipt()['secret_serialized'])
    def test_disallowed_path_cannot_receive_secret(self):
        a=LiveProviderAuthority(self.policy(),environment={'ELEVENLABS_API_KEY':'fixture_secret_123'})
        with self.assertRaisesRegex(ProviderFailure,'PATH_NOT_AUTHORIZED'):a.authorize('GET','/v1/other')
    def test_session_call_budget(self):
        a=LiveProviderAuthority(self.policy(max_session_calls=1),environment={'ELEVENLABS_API_KEY':'fixture_secret_123'})
        a.authorize('GET','/v1/models')
        with self.assertRaisesRegex(ProviderFailure,'SESSION_BUDGET'):a.authorize('GET','/v1/models')
    def test_preflight_call_budget_no_truncation(self):
        with tempfile.TemporaryDirectory() as d:
            _,_,requests,_=setup(Path(d))
            a=LiveProviderAuthority(self.policy(max_session_calls=1),environment={'ELEVENLABS_API_KEY':'fixture_secret_123'})
            self.assertFalse(a.preflight(requests)['truncated'])
            a2=LiveProviderAuthority(self.policy(max_session_calls=1),environment={'ELEVENLABS_API_KEY':'fixture_secret_123'})
            with self.assertRaisesRegex(ProviderFailure,'CALL_BUDGET'):a2.preflight(tuple(requests)*2)
    def test_preflight_character_budget(self):
        with tempfile.TemporaryDirectory() as d:
            _,_,requests,_=setup(Path(d))
            a=LiveProviderAuthority(self.policy(max_session_chars=1),environment={'ELEVENLABS_API_KEY':'fixture_secret_123'})
            with self.assertRaisesRegex(ProviderFailure,'CHARACTER_BUDGET'):a.preflight(requests)
    def test_policy_fingerprint_excludes_secret_value(self):
        p=self.policy();a=LiveProviderAuthority(p,environment={'ELEVENLABS_API_KEY':'fixture_secret_123'})
        self.assertNotIn('fixture_secret_123',p.fingerprint());self.assertEqual(a.receipt()['authority_fingerprint'],p.fingerprint())

if __name__=='__main__':unittest.main()
