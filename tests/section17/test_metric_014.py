from batch004_helpers import DeliveryMetricBase,attach
from copy import deepcopy
@attach
class METRIC014Tests(DeliveryMetricBase):
    task='BIE-EVAL-METRIC-014'
    def test_repeated_attempt_is_not_best_of_n(self):
        r,c,a=self.example();e=deepcopy(c['events'][0]);e['id']='retry';e['time_ms']=90000000;c['events'].append(e);self.reject(r,c,a,code='DUPLICATE_LEARNING_ATTEMPT')
    def test_timestamp_order_is_enforced(self):
        r,c,a=self.example();c['events'][1]['time_ms']=99;self.reject(r,c,a,code='NONMONOTONIC_LEARNING_EVENTS')
    def test_phase_order_not_only_chronological(self):
        r,c,a=self.example();c['events'][0]['question_id']='post-q';c['events'][2]['question_id']='pre-q';self.fail_reason(r,c,a,'LEARNING_PHASE_ORDER_VIOLATION')
    def test_unknown_question_cannot_pad_gain(self):
        r,c,a=self.example();c['events'][0]['question_id']='new';self.reject(r,c,a,code='UNKNOWN_CANDIDATE_ITEM')
    def test_missing_reference_retention_design_blocked(self):
        r,c,a=self.example();r['payload']['questions'].pop();self.reject(r,c,a,code='INCOMPLETE_PAIRED_REFERENCE_DESIGN')
    def test_feedback_reference_must_cover_all_options(self):
        r,c,a=self.example();r['payload']['questions'][0]['feedback_by_option'].pop('A');self.reject(r,c,a,code='REFERENCE_FEEDBACK_INCOMPLETE')
    def test_invalid_reference_correct_option_blocked(self):
        r,c,a=self.example();r['payload']['questions'][0]['correct_option']='C';self.reject(r,c,a,code='ANSWER_KEY_NOT_AN_OPTION')
    def test_exact_gain_computed_not_candidate_reported(self):
        o=self.measure();s=o['details']['statistics']['inverse-square'];self.assertEqual('0',s['pre_accuracy_exact']);self.assertEqual('1',s['paired_gain_exact'])
    def test_candidate_gain_flag_not_accepted(self):
        r,c,a=self.example();c['learning_gain']=1;self.reject(r,c,a)
    def test_no_human_learning_certification(self):self.assertFalse(self.measure()['details']['human_learners_observed'])
