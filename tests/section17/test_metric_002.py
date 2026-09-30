from batch003_helpers import MetricBase,attach_metric_fixtures
from copy import deepcopy
@attach_metric_fixtures
class METRIC002Tests(MetricBase):
    task='BIE-EVAL-METRIC-002'
    def test_facet_type_mismatch(self):
        r,c,a=self.example();c['concepts'][0]['facets']['has_direction']=1;self.assertEqual('3/4',self.measure(r,c,a)['score_exact'])
    def test_extra_facet_is_not_hidden_by_full_recall(self):
        r,c,a=self.example();c['concepts'][0]['facets']['has_no_magnitude']=True;v=self.measure(r,c,a);self.assertEqual('FAIL',v['outcome'])
    def test_duplicate_concept_not_double_counted(self):
        r,c,a=self.example();c['concepts'].append(deepcopy(c['concepts'][0]));self.reject(r,c,a,code='DUPLICATE_METRIC_ITEM')
    def test_unknown_concept_rejected(self):
        r,c,a=self.example();c['concepts'].append({'id':'new','facets':{'x':True}});self.reject(r,c,a,code='UNEXPECTED_METRIC_ITEM')
    def test_empty_candidate_facets_zero_concept_credit(self):
        r,c,a=self.example();c['concepts'][0]['facets']={};self.assertEqual('1/2',self.measure(r,c,a)['score_exact'])
    def test_reference_cannot_have_empty_facets(self):
        r,c,a=self.example();r['payload']['concepts'][0]['facets']={};self.reject(r,c,a)
    def test_relation_endpoint_must_be_reference_concept(self):
        r,c,a=self.example();r['payload']['relations'][0]['to']='missing';self.reject(r,c,a)
    def test_missing_relation_stays_in_denominator(self):
        r,c,a=self.example();c['relations']=[];self.assertEqual('3/4',self.measure(r,c,a)['score_exact'])
    def test_reversed_relation_not_semantically_equal(self):
        r,c,a=self.example();c['relations'][0]['from'],c['relations'][0]['to']=c['relations'][0]['to'],c['relations'][0]['from'];self.assertEqual('3/4',self.measure(r,c,a)['score_exact'])
    def test_list_order_does_not_change_result(self):
        r,c,a=self.example();v=self.measure(r,c,a);c['concepts'].reverse();r['payload']['concepts'].reverse();w=self.measure(r,c,a);self.assertEqual(v['units'],w['units'])
    def test_reference_unit_id_collision_rejected(self):
        r,c,a=self.example();r['payload']['relations'][0]['id']='vector';self.reject(r,c,a)
    def test_no_free_text_entailment_claim(self):
        self.assertFalse(self.measure()['details']['natural_language_semantics'])
