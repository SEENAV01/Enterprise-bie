from batch004_helpers import DeliveryMetricBase,attach
from copy import deepcopy
@attach
class METRIC007Tests(DeliveryMetricBase):
    task='BIE-EVAL-METRIC-007'
    def test_unknown_content_cannot_be_claimed(self):
        r,c,a=self.example();c['activities'][0]['content_id']='invented';self.reject(r,c,a,code='UNKNOWN_CANDIDATE_ITEM')
    def test_zero_objective_weight_blocked(self):
        r,c,a=self.example();r['payload']['objectives'][0]['weight']=0;self.reject(r,c,a)
    def test_missing_reference_assessment_blocked(self):
        r,c,a=self.example();r['payload']['content_bank'].pop();self.reject(r,c,a,code='REFERENCE_ACTIVITY_COVERAGE_MISSING')
    def test_reference_without_practice_is_not_sufficient(self):
        r,c,a=self.example();r['payload']['objectives'][0]['required_kinds']=['explain'];self.reject(r,c,a,code='WEAK_PEDAGOGY_REFERENCE')
    def test_missing_feedback_reference_is_invalid(self):
        r,c,a=self.example();r['payload']['content_bank'][2]['feedback_ids']=[];self.reject(r,c,a,code='REFERENCE_FEEDBACK_REQUIRED')
    def test_duplicate_activity_id_blocked(self):
        r,c,a=self.example();c['activities'].append(deepcopy(c['activities'][0]));self.reject(r,c,a,code='DUPLICATE_METRIC_ITEM')
    def test_zero_duration_activity_blocked(self):
        r,c,a=self.example();c['activities'][0]['end']=0;self.reject(r,c,a,code='EMPTY_OR_REVERSED_INTERVAL')
    def test_claimed_kind_cannot_change_reference_alignment(self):
        r,c,a=self.example();c['activities'][1]['kind']='practice';self.fail_reason(r,c,a,'CONTENT_ALIGNMENT_MISMATCH')
    def test_all_objectives_remain_in_denominator(self):
        r,c,a=self.example();r['payload']['objectives'].append({'id':'other','required_kinds':['explain','practice','assess'],'weight':3})
        for kind in ['explain','practice','assess']:r['payload']['content_bank'].append({'id':'other-'+kind,'objective_id':'other','kind':kind,'feedback_ids':['feedback'] if kind!='explain' else []})
        self.assertEqual('2/5',self.measure(r,c,a)['score_exact'])
    def test_boolean_frame_rejected(self):
        r,c,a=self.example();c['activities'][0]['start']=False;self.reject(r,c,a,code='INTEGER_OUT_OF_PROFILE')
