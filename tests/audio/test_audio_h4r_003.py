"""H4-R1-003 signatures, authority, downgrade/replay and request provenance."""
import unittest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from bie.audio.common import AudioError,fingerprint
from bie.audio.kernel_evidence import validate_kernel_trust,issue_kernel_evaluation
from . import kernel_test_support as k

class SignatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.c=k.context();cls.r=k.actual_receipt()
    def test_actual_signature(self):self.assertEqual(k.verify()['fingerprint'],self.r['payload']['execution']['measurement_fingerprint'])
    def test_exact_signed_request(self):k.verify(request_fingerprint=self.c['request']['fingerprint'])
    def test_request_replay_rejected(self):
        with self.assertRaises(AudioError):k.verify(request_fingerprint='sha256:'+'0'*64)
    def test_legacy_receipt_rejected(self):
        with self.assertRaises(AudioError):k.verify(self.r['payload']['compatibility_receipt'])
    def test_bit_flip_signature(self):
        r=k.clone(self.r);r['signature_ed25519_hex']='0'*128
        with self.assertRaises(AudioError):k.verify(r)
    def test_other_key_signature(self):
        with self.assertRaises(AudioError):k.verify(k.resign(self.r,Ed25519PrivateKey.generate()))
    def test_revoked_issuer(self):
        t=k.clone(self.c['trust']);t['evaluator_trust']['issuers'][0]['revoked']=True
        with self.assertRaises(AudioError):k.verify(trust=t)
    def test_expired_receipt(self):
        with self.assertRaises(AudioError):k.verify(now=self.r['payload']['expires_at'])
    def test_future_receipt(self):
        with self.assertRaises(AudioError):k.verify(now=self.r['payload']['issued_at']-100)
    def test_current_trust_revision_allowed(self):
        t=k.clone(self.c['trust']);t['revision']='new-review';k.verify(trust=t)
    def test_profile_removed(self):
        t=k.clone(self.c['trust']);t['profile_fingerprints']=['sha256:'+'0'*64]
        with self.assertRaises(AudioError):k.verify(trust=t)
    def test_runtime_removed(self):
        t=k.clone(self.c['trust']);t['evaluator_trust']['issuers'][0]['runtime_fingerprints']=['sha256:'+'0'*64]
        with self.assertRaises(AudioError):k.verify(trust=t)
    def test_signer_not_injected(self):
        c=self.c
        with self.assertRaises(AudioError):issue_kernel_evaluation(c['job'],c['mixed'].wav_bytes,c['runtime'],c['profile'],c['trust'],Ed25519PrivateKey.generate(),k.KEY_ID)
    def test_signer_unknown_key_id(self):
        c=self.c
        with self.assertRaises(AudioError):issue_kernel_evaluation(c['job'],c['mixed'].wav_bytes,c['runtime'],c['profile'],c['trust'],c['key'],'OTHER')
    def test_outer_issued_inner_binding(self):
        r=k.clone(self.r);r['payload']['issued_at']+=1
        with self.assertRaises(AudioError):k.verify(k.resign(r))
    def test_resigned_fabricated_namespace(self):
        r=k.clone(self.r);e=r['payload']['execution'];e['kernel_proof']['namespaces']=k.clone(e['host_namespaces'])
        e['fingerprint']=fingerprint({a:b for a,b in e.items() if a!='fingerprint'})
        with self.assertRaises(AudioError):k.verify(k.resign(r))
    def test_resigned_result_hash_invalid(self):
        r=k.clone(self.r);e=r['payload']['execution'];e['result_sha256']='0'*64
        e['fingerprint']=fingerprint({a:b for a,b in e.items() if a!='fingerprint'})
        with self.assertRaises(AudioError):k.verify(k.resign(r))

def _payload_bad(key,value):
    def test(self):
        r=k.clone(self.r);r['payload'][key]=value
        with self.assertRaises((AudioError,TypeError)):k.verify(k.resign(r))
    return test
for _name,_key,_value in [
 ('scope','scope','PRODUCTION_ACCEPTED'),('product','product_accepted',True),
 ('pronunciation','pronunciation_verified',True),('alignment','alignment_accepted',True),
 ('calibration','calibration_status','CALIBRATED'),('boolean_int','product_accepted',0),
 ('schema','schema_version','bie.audio.kernel-evaluator-payload/1'),
 ('profile','profile_fingerprint','sha256:'+'0'*64),('new_field','unknown',True),
 ('request_type','durable_request_fingerprint',True),('time_boolean','issued_at',True)]:
    setattr(SignatureTests,'test_resigned_reject_'+_name,_payload_bad(_key,_value))
