import unittest,tempfile,os
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from bie.audio.common import AudioError,fingerprint,strict_json
from bie.audio.acoustic_contract import AcousticPolicy,build_job
from bie.audio.acoustic_evidence import verify_receipt,validate_trust,load_private_key,issue_evaluation
from .acoustic_test_support import context,clone,rehash,receipt,sign_test_payload,NOW

class EvaluatorAuthenticityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.s,cls.m,cls.j,cls.r,cls.result,cls.key,cls.trust=context()
    def verify(self,r=None,j=None,t=None,now=NOW):return verify_receipt(receipt() if r is None else r,self.j if j is None else j,self.trust if t is None else t,now=now)
    def test_trusted_signature_verifies_current_job(self):self.assertEqual(self.verify(),self.result)
    def test_actual_issue_measures_then_signs(self):
        r=issue_evaluation(self.j,self.m.wav_bytes,self.r,self.key,'test-only-not-production-H2',now=NOW)
        self.assertEqual(self.verify(r),self.result)
    def test_unknown_issuer_cannot_self_register(self):
        r=receipt();r['payload']['key_id']='unknown';r=sign_test_payload(r['payload'])
        with self.assertRaisesRegex(AudioError,'UNKNOWN_ISSUER'):self.verify(r)
    def test_public_key_field_in_envelope_rejected(self):
        r=receipt();r['public_key_hex']=self.trust['issuers'][0]['public_key_hex']
        with self.assertRaises(AudioError):self.verify(r)
    def test_wrong_private_key_rejected(self):
        r=sign_test_payload(receipt()['payload'],Ed25519PrivateKey.generate())
        with self.assertRaisesRegex(AudioError,'SIGNATURE_INVALID'):self.verify(r)
    def test_mutated_payload_rejected(self):
        r=receipt();r['payload']['measurement']['segments'][0]['crop_sha256']='0'*64
        with self.assertRaisesRegex(AudioError,'SIGNATURE_INVALID'):self.verify(r)
    def test_public_rehash_does_not_replace_signature(self):
        r=receipt();r['payload']['measurement']['segments'][0]['crop_sha256']='0'*64;rehash(r['payload']['measurement'])
        with self.assertRaisesRegex(AudioError,'SIGNATURE_INVALID'):self.verify(r)
    def test_truncated_signature(self):
        r=receipt();r['signature_ed25519_hex']=r['signature_ed25519_hex'][:-2]
        with self.assertRaises(AudioError):self.verify(r)
    def test_revoked_key(self):
        t=clone(self.trust);t['issuers'][0]['revoked']=True
        with self.assertRaisesRegex(AudioError,'REVOKED'):self.verify(t=t)
    def test_replaced_trust_public_key(self):
        t=clone(self.trust);t['issuers'][0]['public_key_hex']='1'*64
        with self.assertRaises(AudioError):self.verify(t=t)
    def test_untrusted_model_runtime(self):
        t=clone(self.trust);t['issuers'][0]['runtime_fingerprints']=[fingerprint('other-runtime')]
        with self.assertRaisesRegex(AudioError,'UNTRUSTED_RUNTIME'):self.verify(t=t)
    def test_stale_media_binding(self):
        j=clone(self.j);j['binding']['media_sha256']='1'*64;rehash(j)
        with self.assertRaisesRegex(AudioError,'STALE_BINDING'):self.verify(j=j)
    def test_stale_clock_binding(self):
        j=clone(self.j);j['binding']['clock_fingerprint']=fingerprint('new-clock');rehash(j)
        with self.assertRaisesRegex(AudioError,'STALE_BINDING'):self.verify(j=j)
    def test_stale_voice_binding(self):
        j=clone(self.j);j['segments'][0]['voice_fingerprint']=fingerprint('new-voice');rehash(j)
        with self.assertRaisesRegex(AudioError,'STALE_BINDING'):self.verify(j=j)
    def test_stale_pronunciation_binding(self):
        j=clone(self.j);j['binding']['pronunciation_targets_fingerprint']=fingerprint('new-reading');rehash(j)
        with self.assertRaisesRegex(AudioError,'STALE_BINDING'):self.verify(j=j)
    def test_stale_policy_binding(self):
        j=build_job(self.m,self.s,AcousticPolicy(revision='revised'))
        with self.assertRaisesRegex(AudioError,'STALE_BINDING'):self.verify(j=j)
    def test_expiry_boundary_rejects(self):
        with self.assertRaisesRegex(AudioError,'EXPIRED'):self.verify(now=NOW+600)
    def test_before_expiry_can_reverify(self):self.assertEqual(self.verify(now=NOW+599),self.result)
    def test_future_receipt_rejected(self):
        with self.assertRaisesRegex(AudioError,'FUTURE'):self.verify(receipt(issued=NOW+31))
    def test_key_expired_rejected(self):
        t=clone(self.trust);t['issuers'][0]['not_after']=NOW
        with self.assertRaisesRegex(AudioError,'EXPIRED'):self.verify(t=t)
    def test_wrong_role_rejected(self):
        t=clone(self.trust);t['issuers'][0]['role']='audio-producer'
        with self.assertRaises(AudioError):self.verify(t=t)
    def test_duplicate_issuers_rejected(self):
        t=clone(self.trust);t['issuers'].append(clone(t['issuers'][0]))
        with self.assertRaises(AudioError):self.verify(t=t)
    def test_bool_time_rejected_even_with_signature(self):
        r=receipt();r['payload']['issued_at']=True;r=sign_test_payload(r['payload'])
        with self.assertRaises(AudioError):self.verify(r)
    def test_product_authority_rejected_even_with_signature(self):
        r=receipt();r['payload']['product_accepted']=True;r=sign_test_payload(r['payload'])
        with self.assertRaises(AudioError):self.verify(r)
    def test_omitted_segment_rejected_even_with_signature(self):
        r=receipt();r['payload']['measurement']['segments'].pop();rehash(r['payload']['measurement']);r=sign_test_payload(r['payload'])
        with self.assertRaises(AudioError):self.verify(r)
    def test_forged_phone_metric_rejected_even_with_signature(self):
        r=receipt();r['payload']['measurement']['segments'][0]['phone_comparisons'][0]['minimum_edit_distance']=999;rehash(r['payload']['measurement']);r=sign_test_payload(r['payload'])
        with self.assertRaises(AudioError):self.verify(r)
    def test_key_permissions_and_private_read(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'private.key';p.write_bytes(self.key.private_bytes_raw());p.chmod(0o600)
            self.assertEqual(load_private_key(p).public_key().public_bytes_raw(),self.key.public_key().public_bytes_raw())
            p.chmod(0o644)
            with self.assertRaises(AudioError):load_private_key(p)
    def test_key_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'real';p.write_bytes(self.key.private_bytes_raw());p.chmod(0o600);q=Path(td)/'link';q.symlink_to(p)
            with self.assertRaises(AudioError):load_private_key(q)
    def test_private_key_invalid_size_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'key';p.write_bytes(b'no-key');p.chmod(0o600)
            with self.assertRaises(AudioError):load_private_key(p)
    def test_duplicate_json_fields_rejected(self):
        with self.assertRaises(AudioError):strict_json('{"key_id":"a","key_id":"b"}')
    def test_bool_metric_rejected_even_with_signature(self):
        r=receipt();p=r['payload']['measurement']['segments'][0]['phone_comparisons'][0]
        p['selected_variant_index']=False;rehash(r['payload']['measurement']);r=sign_test_payload(r['payload'])
        with self.assertRaises(AudioError):self.verify(r)
