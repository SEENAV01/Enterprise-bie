from batch004_helpers import DeliveryMetricBase,attach
from bie.evaluation.benchmarks.models import digest
@attach
class METRIC012Tests(DeliveryMetricBase):
    task='BIE-EVAL-METRIC-012'
    def test_required_audio_absent_fails(self):
        r,c,a=self.example();r['payload']['targets'][0]['audio_required']=True;self.fail_reason(r,c,a,'REQUIRED_AUDIO_STREAM_MISSING')
    def test_wrong_frame_count_fails(self):
        r,c,a=self.example();r['payload']['targets'][0]['frame_count']=13;self.fail_reason(r,c,a,'RENDER_FRAME_COUNT_MISMATCH')
    def test_one_frame_tolerance_not_allowed(self):
        r,c,a=self.example();r['payload']['targets'][0]['pts_tolerance_seconds']='1/6';self.reject(r,c,a,code='TIMESTAMP_TOLERANCE_TOO_LARGE')
    def test_nonmonotonic_pts_fails(self):
        r,c,a=self.example();o=a['render'];o['facts']['pts_seconds'][1]='0';o['receipt_sha256']=digest({k:v for k,v in o.items() if k!='receipt_sha256'});self.fail_reason(r,c,a,'RENDER_TIMESTAMPS_MISMATCH')
    def test_missing_frame_hashes_blocked(self):
        r,c,a=self.example();o=a['render'];o['facts']['frame_sha256'].pop();o['receipt_sha256']=digest({k:v for k,v in o.items() if k!='receipt_sha256'});self.reject(r,c,a,code='MEDIA_OBSERVATION_INCONSISTENT')
    def test_forged_media_receipt_hash_blocked(self):
        r,c,a=self.example();a['render']['receipt_sha256']='0'*64;self.reject(r,c,a,code='OBSERVATION_HASH_MISMATCH')
    def test_container_duration_mismatch_fails(self):
        r,c,a=self.example();o=a['render'];o['facts']['container_duration']='3';o['receipt_sha256']=digest({k:v for k,v in o.items() if k!='receipt_sha256'});self.fail_reason(r,c,a,'RENDER_DURATION_MISMATCH')
    def test_boolean_audio_requirement_really_typed(self):
        r,c,a=self.example();r['payload']['targets'][0]['audio_required']='false';self.reject(r,c,a,code='BOOLEAN_REQUIRED')
    def test_empty_media_candidates_cannot_score_one(self):
        r,c,a=self.example();c['artifacts']=[];a.clear();self.assertEqual('0',self.measure(r,c,a)['score_exact'])
    def test_decode_does_not_claim_audio_content(self):self.assertFalse(self.measure()['details']['audio_content_decoded'])
