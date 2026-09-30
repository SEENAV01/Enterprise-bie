from batch004_helpers import DeliveryMetricBase,attach
from bie.evaluation.benchmarks.models import digest
@attach
class METRIC016Tests(DeliveryMetricBase):
    task='BIE-EVAL-METRIC-016'
    def test_minimum_one_run_reference_rejected(self):
        r,c,a=self.example();r['payload']['minimum_runs']=1;self.reject(r,c,a,code='INTEGER_OUT_OF_PROFILE')
    def test_duplicate_observation_id_rejected(self):
        r,c,a=self.example();c['observation_ids']=['first','first'];self.reject(r,c,a,code='DUPLICATE_METRIC_ITEM')
    def test_reference_output_traversal_rejected(self):
        r,c,a=self.example();r['payload']['outputs'][0]['path']='../secret';self.reject(r,c,a,code='UNSAFE_OUTPUT_PATH')
    def test_manifest_subject_binding_verified(self):
        r,c,a=self.example();o=a['second'];o['subject_sha256']='0'*64;o['receipt_sha256']=digest({k:v for k,v in o.items() if k!='receipt_sha256'});self.reject(r,c,a,code='OUTPUT_MANIFEST_SUBJECT_MISMATCH')
    def test_added_output_is_not_ignored(self):
        r,c,a=self.example();o=a['second'];o['facts']['outputs'].append({'path':'extra.txt','sha256':'0'*64,'bytes':0});o['subject_sha256']=digest(o['facts']['outputs']);o['receipt_sha256']=digest({k:v for k,v in o.items() if k!='receipt_sha256'});self.fail_reason(r,c,a,'REPRODUCIBILITY_OUTPUT_ROSTER_MISMATCH')
    def test_casefold_output_collisions_blocked(self):
        r,c,a=self.example();r['payload']['outputs'].append({'id':'collision','path':'LESSON.PYC','weight':1});self.reject(r,c,a,code='DUPLICATE_REFERENCE_OUTPUT_PATH')
    def test_different_byte_size_fails_even_same_hash(self):
        r,c,a=self.example();o=a['second'];o['facts']['outputs'][0]['bytes']+=1;o['subject_sha256']=digest(o['facts']['outputs']);o['receipt_sha256']=digest({k:v for k,v in o.items() if k!='receipt_sha256'});self.fail_reason(r,c,a,'OUTPUT_BYTES_NOT_REPRODUCIBLE')
    def test_unclaimed_observation_rejected(self):
        r,c,a=self.example();a['extra']=a['second'];self.reject(r,c,a,code='UNUSED_OR_MISSING_OBSERVATIONS')
    def test_zero_runs_is_not_vacuously_reproducible(self):
        r,c,a=self.example();c['observation_ids']=[];a.clear();self.assertEqual('0',self.measure(r,c,a)['score_exact'])
    def test_hashing_does_not_prove_build_execution(self):self.assertFalse(self.measure()['details']['build_execution_proven_by_hashing_alone'])
