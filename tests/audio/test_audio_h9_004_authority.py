import unittest,base64
from dataclasses import replace
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from bie.audio.common import AudioError
from bie.audio.evaluator_authority import AuthorityPayload,AuthorityTrust,SignedAuthority,sign_authority,verify_authority
from tests.audio.h9_test_support import *

class AuthorityTests(unittest.TestCase):
    def test_production_authority(self):
        p=profile(); c=calibration(p); s,t=authority(p,c); self.assertTrue(verify_authority(s,t,p,c,now=NOW)['production_authorized'])
    def test_test_role_not_production(self):
        p=profile(); c=calibration(p); s,t=authority(p,c,production=False,custody='EPHEMERAL_TEST'); self.assertFalse(verify_authority(s,t,p,c,now=NOW)['production_authorized'])
    def test_test_fixture_calibration_not_production(self):
        p=profile(); c=calibrate(dataset(p,scope='TEST_FIXTURE_ONLY',held=False,independent=False)); s,t=authority(p,c); self.assertFalse(verify_authority(s,t,p,c,now=NOW)['production_authorized'])
    def test_local_file_custody_not_production(self):
        p=profile(); c=calibration(p); s,t=authority(p,c,custody='LOCAL_FILE'); self.assertFalse(verify_authority(s,t,p,c,now=NOW)['production_authorized'])
    def test_trust_must_allow_production(self):
        p=profile(); c=calibration(p); s,t=authority(p,c,allow=False); self.assertFalse(verify_authority(s,t,p,c,now=NOW)['production_authorized'])
    def test_signature_tamper_rejected(self):
        p=profile(); c=calibration(p); s,t=authority(p,c); raw=bytearray(base64.b64decode(s.signature_b64)); raw[0]^=1
        with self.assertRaisesRegex(AudioError,'EVALUATOR_AUTHORITY_SIGNATURE'): verify_authority(replace(s,signature_b64=base64.b64encode(raw).decode()),t,p,c,now=NOW)
    def test_wrong_key_rejected(self):
        p=profile(); c=calibration(p); s,t=authority(p,c); key=Ed25519PrivateKey.generate(); pub=key.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
        bad=replace(t,public_key_b64=base64.b64encode(pub).decode())
        with self.assertRaisesRegex(AudioError,'EVALUATOR_AUTHORITY_SIGNATURE'): verify_authority(s,bad,p,c,now=NOW)
    def test_wrong_issuer_rejected(self):
        p=profile(); c=calibration(p); s,t=authority(p,c)
        with self.assertRaisesRegex(AudioError,'EVALUATOR_AUTHORITY_TRUST'): verify_authority(s,replace(t,issuer_id='x'),p,c,now=NOW)
    def test_profile_binding(self):
        p=profile(); c=calibration(p); s,t=authority(p,c); p2=replace(p,model_revision='r2')
        with self.assertRaisesRegex(AudioError,'EVALUATOR_AUTHORITY_BINDING'): verify_authority(s,t,p2,c,now=NOW)
    def test_calibration_binding(self):
        p=profile(); c=calibration(p); s,t=authority(p,c); c2=replace(c,threshold_ppm=c.threshold_ppm+1)
        with self.assertRaisesRegex(AudioError,'EVALUATOR_AUTHORITY_BINDING'): verify_authority(s,t,p,c2,now=NOW)
    def test_expired_rejected(self):
        p=profile(); c=calibration(p); s,t=authority(p,c)
        with self.assertRaisesRegex(AudioError,'EVALUATOR_AUTHORITY_FRESHNESS'): verify_authority(s,t,p,c,now=NOW+7200)
    def test_future_rejected(self):
        p=profile(); c=calibration(p); s,t=authority(p,c)
        with self.assertRaisesRegex(AudioError,'EVALUATOR_AUTHORITY_FRESHNESS'): verify_authority(s,t,p,c,now=NOW-1000)
    def test_payload_requires_external_custody_literal(self):
        p=profile(); c=calibration(p)
        with self.assertRaisesRegex(AudioError,'EVALUATOR_AUTHORITY_CUSTODY'): AuthorityPayload('i','TEST_ONLY','k','magic',p.fingerprint(),c.fingerprint(),'test',NOW,NOW+1,('x',))
    def test_verified_nonproduction_scope(self):
        p=profile(); c=calibration(p); s,t=authority(p,c,production=False,custody='EPHEMERAL_TEST'); self.assertEqual(verify_authority(s,t,p,c,now=NOW)['scope'],'VERIFIED_NON_PRODUCTION')

if __name__=='__main__': unittest.main()
