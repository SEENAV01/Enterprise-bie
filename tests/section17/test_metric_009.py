from batch004_helpers import DeliveryMetricBase,attach
@attach
class METRIC009Tests(DeliveryMetricBase):
    task='BIE-EVAL-METRIC-009'
    def test_box_touching_viewport_edge_passes(self):
        r,c,a=self.example();c['objects'][1]['box']['x']=100;self.assertEqual('PASS',self.measure(r,c,a)['outcome'])
    def test_touching_boxes_are_not_occluded(self):
        r,c,a=self.example();c['objects'][1]['box']['x']=30;self.assertEqual('PASS',self.measure(r,c,a)['outcome'])
    def test_zero_box_width_blocked(self):
        r,c,a=self.example();c['objects'][0]['box']['width']=0;self.reject(r,c,a)
    def test_bad_reference_endpoint_blocked(self):
        r,c,a=self.example();r['payload']['relations'][0]['to']='missing';self.reject(r,c,a,code='REFERENCE_RELATION_ENDPOINT_MISSING')
    def test_unknown_candidate_relation_blocked(self):
        r,c,a=self.example();c['relations'][0]['id']='other';self.reject(r,c,a,code='UNKNOWN_CANDIDATE_ITEM')
    def test_duplicate_nonoverlap_pair_blocked(self):
        r,c,a=self.example();r['payload']['nonoverlap_pairs'].append({'first':'b','second':'a'});self.reject(r,c,a,code='DUPLICATE_NONOVERLAP_PAIR')
    def test_alt_text_blank_not_accepted(self):
        r,c,a=self.example();c['objects'][0]['alt_text']='';self.reject(r,c,a,code='INVALID_TEXT')
    def test_negative_y_fails_visibility(self):
        r,c,a=self.example();c['objects'][0]['box']['y']=-1;self.fail_reason(r,c,a,'OBJECT_OUTSIDE_VIEWPORT')
    def test_missing_relation_remains_denominator(self):
        r,c,a=self.example();c['relations']=[];self.assertEqual('2/3',self.measure(r,c,a)['score_exact'])
    def test_semantic_type_mismatch_not_label_match(self):
        r,c,a=self.example();c['objects'][0]['kind']='decoration';self.fail_reason(r,c,a,'SEMANTIC_REPRESENTATION_MISMATCH')
