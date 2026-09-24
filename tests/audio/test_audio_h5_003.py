import unittest,time
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from bie.audio.common import AudioError
from bie.audio.pipeline_evidence import authorize,validate_trust,SCHEMA
from .pipeline_test_support import context,actual,clone,verify,resign,request

class Evidence(unittest.TestCase):
    def test_01_current_signature_valid(self):self.assertTrue(verify()['signature_reverified'])
    def test_02_wrong_signature(self):
        _,r=actual();r=clone(r);r['signature_ed25519_hex']='0'*128
        with self.assertRaises(AudioError):verify(receipt=r)
    def test_03_wrong_signature_domain(self):
        from bie.audio.acoustic_contract import canonical
        _,r=actual();r=clone(r);r['signature_ed25519_hex']=context()['key'].sign(b'OTHER'+canonical(r['payload'])).hex()
        with self.assertRaises(AudioError):verify(receipt=r)
    def test_04_algorithm_relabel(self):
        _,r=actual();r=clone(r);r['schema_version']='bie.audio.signed-kernel-evaluation/2'
        with self.assertRaises(AudioError):verify(receipt=r)
    def test_05_revoked_executor(self):
        t=clone(context()['trust']);t['issuers'][0]['revoked']=True
        with self.assertRaises(AudioError):verify(trust=t)
    def test_06_unapproved_profile(self):
        t=clone(context()['trust']);t['issuers'][0]['profile_fingerprints']=['sha256:'+'0'*64]
        with self.assertRaises(AudioError):verify(trust=t)
    def test_07_wrong_role(self):
        t=clone(context()['trust']);t['issuers'][0]['role']='acoustic-evaluator'
        with self.assertRaises(AudioError):verify(trust=t)
    def test_08_wrong_issuer_key(self):
        t=clone(context()['trust']);t['issuers'][0]['public_key_hex']='1'*64
        with self.assertRaises(AudioError):verify(trust=t)
    def test_09_expired_receipt(self):
        _,r=actual()
        with self.assertRaises(AudioError):verify(now=r['payload']['expires_at'])
    def test_10_future_issue_time(self):
        # Bind the assertion to the receipt's original verification clock.  A full
        # section regression may legitimately run for several minutes before this
        # test, so wall-clock time must not turn the intentionally future-dated
        # receipt into a current one and make the test order-dependent.
        _,r=actual();verification_clock=r['payload']['issued_at'];r=clone(r)
        r['payload']['issued_at']+=120;r['payload']['expires_at']+=120
        with self.assertRaises(AudioError):verify(receipt=resign(r),now=verification_clock)
    def test_11_signature_cannot_escalate_product_acceptance(self):
        _,r=actual();r=clone(r);r['payload']['product_accepted']=True
        with self.assertRaises(AudioError):verify(receipt=resign(r))
    def test_12_signature_cannot_escalate_pronunciation(self):
        _,r=actual();r=clone(r);r['payload']['pronunciation_verified']=True
        with self.assertRaises(AudioError):verify(receipt=resign(r))
    def test_13_run_label_bound(self):
        with self.assertRaises(AudioError):verify(request_value=request(run_id='01952504-3824-4000-8000-000000000006'))
    def test_14_job_label_bound(self):
        with self.assertRaises(AudioError):verify(request_value=request(job_id='another'))
    def test_15_revision_bound(self):
        with self.assertRaises(AudioError):verify(request_value=request(revision='r2'))
    def test_16_duplicate_issuer(self):
        t=clone(context()['trust']);t['issuers'].append(clone(t['issuers'][0]))
        with self.assertRaises(AudioError):validate_trust(t)
    def test_17_malformed_public_key(self):
        t=clone(context()['trust']);t['issuers'][0]['public_key_hex']='nothex'
        with self.assertRaises(AudioError):validate_trust(t)
    def test_18_wrong_signer_rejected_before_execution(self):
        c=context()
        with self.assertRaises(AudioError):authorize(c['profile'],c['trust'],c['request']['key_id'],signer=Ed25519PrivateKey.generate())
    def test_19_current_policy_age_rechecked(self):
        t=clone(context()['trust']);t['max_age_seconds']=1
        with self.assertRaises(AudioError):verify(trust=t)
    def test_20_issuer_expiry_rechecked(self):
        t=clone(context()['trust']);t['issuers'][0]['not_after']=int(time.time())-1
        with self.assertRaises(AudioError):verify(trust=t)
    def test_21_signature_not_inferred_from_hash(self):
        _,r=actual();r=clone(r);r.pop('signature_ed25519_hex')
        with self.assertRaises(AudioError):verify(receipt=r)
    def test_22_boolean_issue_time_rejected(self):
        _,r=actual();r=clone(r);r['payload']['issued_at']=True
        with self.assertRaises(AudioError):verify(receipt=resign(r))

    def test_23_fractional_lease_clock_supported(self):
        from .pipeline_test_support import actual,verify
        receipt=actual()[1];when=receipt['payload']['issued_at']+0.5
        self.assertTrue(verify(now=when)['signature_reverified'])
    def test_24_invalid_verification_clocks_rejected(self):
        from .pipeline_test_support import verify
        for when in (True,float('nan'),float('inf'),-1,'100'):
            with self.subTest(when=when),self.assertRaises(AudioError):verify(now=when)
    def test_25_fractional_after_expiry_is_rejected(self):
        from .pipeline_test_support import actual,verify
        with self.assertRaises(AudioError):verify(now=actual()[1]['payload']['expires_at']+0.01)
