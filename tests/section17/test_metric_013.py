from batch004_helpers import DeliveryMetricBase,attach
from bie.evaluation.benchmarks.models import digest
from bie.evaluation.benchmarks.metrics.frame_quality import pixels
from copy import deepcopy
@attach
class METRIC013Tests(DeliveryMetricBase):
    task='BIE-EVAL-METRIC-013'
    def test_lossless_pixels_have_zero_mae(self):
        for row in self.measure()['details']['statistics'].values():self.assertEqual('0',row['mae_exact'])
    def test_duplicate_reference_frame_index_blocked(self):
        r,c,a=self.example();r['payload']['frames'][1]['index']=0;self.reject(r,c,a,code='DUPLICATE_REFERENCE_FRAME_INDEX')
    def test_unknown_motion_endpoint_blocked(self):
        r,c,a=self.example();r['payload']['motion_pairs'][0]['second']='frame:200';self.reject(r,c,a,code='INVALID_MOTION_PAIR')
    def test_invalid_base64_blocked(self):
        r,c,a=self.example();r['payload']['frames'][0]['rgb_base64']='@@';self.reject(r,c,a,code='INVALID_PIXEL_ENCODING')
    def test_wrong_reference_pixel_size_blocked(self):
        r,c,a=self.example();r['payload']['frames'][0]['width']=1;self.reject(r,c,a,code='PIXEL_PAYLOAD_INTEGRITY_FAILURE')
    def test_duplicate_decoded_frame_index_blocked(self):
        r,c,a=self.example();o=a['frames'];o['facts']['frames'][1]['index']=0;o['receipt_sha256']=digest({k:v for k,v in o.items() if k!='receipt_sha256'});self.reject(r,c,a,code='DUPLICATE_DECODED_FRAME_INDEX')
    def test_unrequested_sample_blocked(self):
        r,c,a=self.example();o=a['frames'];row=deepcopy(o['facts']['frames'][1]);row['id']='extra';o['facts']['frames'].append(row);o['receipt_sha256']=digest({k:v for k,v in o.items() if k!='receipt_sha256'});self.reject(r,c,a,code='UNREQUESTED_FRAME_OBSERVATION')
    def test_max_black_fraction_bounded(self):
        r,c,a=self.example();r['payload']['frames'][0]['max_black_fraction']=2;self.reject(r,c,a)
    def test_empty_frames_reference_blocked(self):
        r,c,a=self.example();r['payload']['frames']=[];self.reject(r,c,a)
    def test_duplicate_motion_pair_blocked(self):
        r,c,a=self.example();r['payload']['motion_pairs']*=2;self.reject(r,c,a,code='DUPLICATE_MOTION_PAIR')
