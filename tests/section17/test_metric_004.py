from batch003_helpers import MetricBase,attach_metric_fixtures
@attach_metric_fixtures
class METRIC004Tests(MetricBase):
    task='BIE-EVAL-METRIC-004'
    def test_forward_reference_cannot_prove_goal(self):
        r,c,a=self.example();c['steps'].reverse();v=self.measure(r,c,a);self.assertEqual('1/3',v['score_exact']);self.assertIn('UNPROVED_OR_FORWARD_PREMISE',self.reasons(v))
    def test_invalid_step_cannot_be_reused(self):
        r,c,a=self.example();c['steps'][0]['premises']=['f2'];v=self.measure(r,c,a);self.assertEqual('0',v['score_exact']);self.assertIn('UNPROVED_OR_FORWARD_PREMISE',self.reasons(v))
    def test_step_cannot_shadow_trusted_fact(self):
        r,c,a=self.example();c['steps'][0]['id']='f1';self.reject(r,c,a,code='STEP_SHADOWS_TRUSTED_PREMISE')
    def test_circular_self_reference_fails(self):
        r,c,a=self.example();c['steps'][0]['premises']=['s1'];self.assertEqual('0',self.measure(r,c,a)['score_exact'])
    def test_candidate_cannot_insert_axiom(self):
        r,c,a=self.example();c['facts']=[{'id':'own','atom':'S'}];self.reject(r,c,a)
    def test_wrong_conclusion_not_credited(self):
        r,c,a=self.example();c['steps'][0]['conclusion']='S';self.assertIn('RULE_CONCLUSION_MISMATCH',self.reasons(self.measure(r,c,a)))
    def test_fact_goal_does_not_need_new_derivation(self):
        r,c,a=self.example();r['payload']['goals']=[{'id':'g','atom':'P','weight':1}];c['steps']=[];self.assertEqual('PASS',self.measure(r,c,a)['outcome'])
    def test_duplicate_premise_id_rejected(self):
        r,c,a=self.example();c['steps'][0]['premises']=['f1','f1'];self.reject(r,c,a,code='DUPLICATE_METRIC_ITEM')
    def test_rule_requires_all_antecedents_not_any(self):
        r,c,a=self.example();c['steps'][1]['premises']=['f2'];self.assertEqual('1/3',self.measure(r,c,a)['score_exact'])
    def test_premise_order_irrelevant(self):
        r,c,a=self.example();c['steps'][1]['premises'].reverse();self.assertEqual('PASS',self.measure(r,c,a)['outcome'])
    def test_extra_irrelevant_premise_is_not_licensed_rule(self):
        r,c,a=self.example();c['steps'][0]['premises'].append('f2');self.assertEqual('FAIL',self.measure(r,c,a)['outcome'])
    def test_general_reasoning_not_claimed(self):self.assertFalse(self.measure()['details']['general_reasoning_judgment'])
