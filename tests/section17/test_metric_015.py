from batch004_helpers import DeliveryMetricBase,attach
from bie.evaluation.benchmarks.metrics.accessibility import contrast,luminance
@attach
class METRIC015Tests(DeliveryMetricBase):
    task='BIE-EVAL-METRIC-015'
    def test_black_white_contrast_is_21(self):self.assertEqual(21,contrast([0,0,0],[255,255,255]))
    def test_same_color_contrast_is_one(self):self.assertEqual(1,contrast([12,24,36],[12,24,36]))
    def test_standard_text_777777_is_below_4_5(self):
        r,c,a=self.example();c['text_styles'][0].update(foreground=[119]*3,background=[255]*3);self.fail_reason(r,c,a,'TEXT_CONTRAST_BELOW_FLOOR')
    def test_trusted_large_text_777777_can_pass(self):
        r,c,a=self.example();r['payload']['text_labels'][0]['large_text']=True;c['text_styles'][0].update(foreground=[119]*3,background=[255]*3);self.assertEqual('PASS',self.measure(r,c,a)['outcome'])
    def test_candidate_cannot_claim_large_text_exception(self):
        r,c,a=self.example();c['text_styles'][0]['large_text']=True;self.reject(r,c,a)
    def test_out_of_range_rgb_rejected(self):
        r,c,a=self.example();c['text_styles'][0]['foreground']=[256,0,0];self.reject(r,c,a)
    def test_split_caption_coverage_and_text(self):
        r,c,a=self.example();c['captions']=[{'id':'c1','speech_id':'speech','start':0,'end':1000,'text':'Distance changes'},{'id':'c2','speech_id':'speech','start':1000,'end':2000,'text':'force'}];self.assertEqual('PASS',self.measure(r,c,a)['outcome'])
    def test_focus_reference_missing_target_blocked(self):
        r,c,a=self.example();c['controls'][0]['next_id']='missing';self.reject(r,c,a,code='BROKEN_FOCUS_REFERENCE')
    def test_missing_accessible_name_blocked(self):
        r,c,a=self.example();c['controls'][0]['accessible_name']='';self.reject(r,c,a,code='INVALID_TEXT')
    def test_no_wcag_certification_in_report(self):self.assertFalse(self.measure()['details']['wcag_conformance_certified'])
