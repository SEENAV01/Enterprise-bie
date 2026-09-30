from batch003_helpers import MetricBase,attach_metric_fixtures
from bie.evaluation.benchmarks.metrics.causality import model,evaluate_model
from fractions import Fraction
@attach_metric_fixtures
class METRIC006Tests(MetricBase):
    task='BIE-EVAL-METRIC-006'
    def test_do_overrides_incoming_equation_not_exogenous_parent(self):
        r,c,a=self.example();n,t,o,e=model(r['payload']['model']);v=evaluate_model(n,t,o,{'X':0});self.assertEqual(Fraction(2),v['U']);self.assertEqual(Fraction(8),v['Y'])
    def test_observation_without_intervention_different_from_do(self):
        r,c,a=self.example();n,t,o,e=model(r['payload']['model']);v=evaluate_model(n,t,o,{});self.assertEqual(Fraction(14),v['Y'])
    def test_intervene_on_outcome_replaces_parents(self):
        r,c,a=self.example();n,t,o,e=model(r['payload']['model']);self.assertEqual(Fraction(99),evaluate_model(n,t,o,{'Y':99})['Y'])
    def test_unknown_intervention_rejected(self):
        r,c,a=self.example();r['payload']['queries'][0]['interventions']={'unknown':1};self.reject(r,c,a,code='UNKNOWN_INTERVENTION_NODE')
    def test_reference_cycle_rejected(self):
        r,c,a=self.example();r['payload']['model'][0]['parents']=[{'node':'Y','coefficient':1}];self.reject(r,c,a,code='CYCLIC_REFERENCE_GRAPH')
    def test_zero_coefficient_not_an_edge(self):
        r,c,a=self.example();r['payload']['model'][1]['parents'][0]['coefficient']=0;self.reject(r,c,a,code='ZERO_COEFFICIENT_EDGE')
    def test_duplicate_reported_edge_rejected(self):
        r,c,a=self.example();c['edges'].append(dict(c['edges'][0]));self.reject(r,c,a,code='DUPLICATE_GRAPH_EDGE')
    def test_extra_edge_is_fail_even_when_queries_correct(self):
        r,c,a=self.example();c['edges'].append({'from':'Y','to':'U'});v=self.measure(r,c,a);self.assertEqual('1',v['score_exact']);self.assertEqual('FAIL',v['outcome'])
    def test_query_absence_not_remove_denominator(self):
        r,c,a=self.example();c['queries']=[];self.assertEqual('1/2',self.measure(r,c,a)['score_exact'])
    def test_fixed_noise_preserved_for_counterfactual(self):
        r,c,a=self.example();r['payload']['model'][2]['noise']=5;c['queries'][0]['value']=13;c['queries'][1]['value']=16;self.assertEqual('PASS',self.measure(r,c,a)['outcome'])
    def test_structural_node_input_order_irrelevant(self):
        r,c,a=self.example();v=self.measure(r,c,a);r['payload']['model'].reverse();self.assertEqual(v['units'],self.measure(r,c,a)['units'])
    def test_negative_coefficient_supported(self):
        r,c,a=self.example();r['payload']['model'][2]['parents'][0]['coefficient']=-3;c['queries'][1]['value']=5;self.assertEqual('PASS',self.measure(r,c,a)['outcome'])
    def test_unknown_candidate_node_rejected(self):
        r,c,a=self.example();c['edges'][0]['to']='missing';self.reject(r,c,a,code='UNKNOWN_CANDIDATE_NODE')
    def test_no_empirical_causal_certification(self):self.assertFalse(self.measure()['details']['independent_causal_validation'])
