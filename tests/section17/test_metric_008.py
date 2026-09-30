from batch004_helpers import DeliveryMetricBase,attach
from copy import deepcopy
@attach
class METRIC008Tests(DeliveryMetricBase):
    task='BIE-EVAL-METRIC-008'
    def test_cyclic_reference_precedence_blocked(self):
        r,c,a=self.example();r['payload']['precedence'].append({'before':'recap','after':'question'});self.reject(r,c,a,code='CYCLIC_REFERENCE_GRAPH')
    def test_duplicate_beat_occurrence_fails(self):
        r,c,a=self.example();c['scenes'][1]['beats'].append('question');self.fail_reason(r,c,a,'DUPLICATE_BEAT')
    def test_unscored_scene_cannot_hide_dense_text(self):
        r,c,a=self.example();c['scenes'].append({'id':'extra','start':0,'end':1,'beats':[],'narration':'many many many words','focus_ids':[]});self.fail_reason(r,c,a,'NARRATION_DENSITY_EXCEEDED')
    def test_unknown_focus_rejected(self):
        r,c,a=self.example();c['scenes'][0]['focus_ids'].append('invented');self.reject(r,c,a,code='UNKNOWN_FOCUS_CONCEPT')
    def test_exact_density_floor_passes(self):
        r,c,a=self.example();c['scenes'][0]['narration']=' '.join(['word']*15);self.assertEqual('PASS',self.measure(r,c,a)['outcome'])
    def test_one_extra_word_over_floor_fails(self):
        r,c,a=self.example();c['scenes'][0]['narration']=' '.join(['word']*16);self.fail_reason(r,c,a,'NARRATION_DENSITY_EXCEEDED')
    def test_scene_outside_duration_rejected(self):
        r,c,a=self.example();c['scenes'][2]['end']=361;self.reject(r,c,a,code='INTEGER_OUT_OF_PROFILE')
    def test_empty_narration_rejected(self):
        r,c,a=self.example();c['scenes'][0]['narration']=' ';self.reject(r,c,a,code='INVALID_TEXT')
    def test_overlapping_scenes_fail(self):
        r,c,a=self.example();c['scenes'][1]['start']=119;self.fail_reason(r,c,a,'OVERLAPPING_SCENES')
    def test_unknown_beat_rejected(self):
        r,c,a=self.example();c['scenes'][0]['beats']=['new'];self.reject(r,c,a,code='UNKNOWN_CANDIDATE_ITEM')
