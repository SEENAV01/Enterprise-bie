from batch004_helpers import DeliveryMetricBase,attach
from bie.evaluation.benchmarks.models import digest
@attach
class METRIC011Tests(DeliveryMetricBase):
    task='BIE-EVAL-METRIC-011'
    def test_tampered_receipt_not_rehashed_blocked(self):
        r,c,a=self.example();a['python']['facts']['exit_code']=7;self.reject(r,c,a,code='OBSERVATION_HASH_MISMATCH')
    def test_candidate_owned_pass_flag_rejected(self):
        r,c,a=self.example();c['passed']=True;self.reject(r,c,a)
    def test_empty_reference_targets_blocked(self):
        r,c,a=self.example();r['payload']['targets']=[];self.reject(r,c,a)
    def test_extra_observation_not_silently_ignored(self):
        r,c,a=self.example();a['unused']=a['python'];self.reject(r,c,a,code='UNUSED_OR_MISSING_OBSERVATIONS')
    def test_compiler_language_profile_mismatch_fails(self):
        r,c,a=self.example();r['payload']['targets'][0]['language']='typescript';self.fail_reason(r,c,a,'COMPILER_PROFILE_MISMATCH')
    def test_unknown_compiler_profile_rejected(self):
        r,c,a=self.example();r['payload']['targets'][0]['language']='shell';self.reject(r,c,a)
    def test_boolean_exit_code_blocked(self):
        r,c,a=self.example();o=a['python'];o['facts']['exit_code']=False;o['receipt_sha256']=digest({k:v for k,v in o.items() if k!='receipt_sha256'});self.reject(r,c,a,code='INTEGER_OUT_OF_PROFILE')
    def test_zero_emitted_bytes_cannot_pass(self):
        r,c,a=self.example();o=a['python'];o['facts']['output_bytes']=0;o['receipt_sha256']=digest({k:v for k,v in o.items() if k!='receipt_sha256'});self.fail_reason(r,c,a,'COMPILED_ARTIFACT_MISSING')
    def test_negative_byte_count_rejected(self):
        r,c,a=self.example();o=a['python'];o['facts']['output_bytes']=-1;o['receipt_sha256']=digest({k:v for k,v in o.items() if k!='receipt_sha256'});self.reject(r,c,a)
    def test_metric_does_not_claim_runtime_or_remotion(self):
        d=self.measure()['details'];self.assertFalse(d['candidate_runtime_executed']);self.assertFalse(d['remotion_bundle_verified'])
