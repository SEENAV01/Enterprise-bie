import unittest
from copy import deepcopy
from bie.evaluation.benchmarks.models import BenchmarkError,digest
from bie.evaluation.benchmarks.release.thresholds import evaluate
class EnterpriseThreshold001(unittest.TestCase):
    def setUp(self):
        self.p={'id':'p','version':'1.0.0','minimum_score':'4/5','minimum_measured_fraction':'1','metrics':[{'id':'a','weight':'3'},{'id':'b','weight':'1'}]}
        self.rows=[{'id':'a','status':'MEASURED','score':'1'},{'id':'b','status':'MEASURED','score':'1/5'}]
    def run_gate(self,pin=None):return evaluate(self.p,self.rows,expected_policy_sha256=digest(self.p) if pin is None else pin)
    def test_exact_weighted_boundary_passes(self):self.assertEqual('PASS',self.run_gate()['outcome']);self.assertEqual('4/5',self.run_gate()['score_exact'])
    def test_below_threshold_fails(self):self.rows[1]['score']='19/100';self.assertEqual('FAIL',self.run_gate()['outcome'])
    def test_missing_keeps_fixed_denominator(self):self.rows.pop();self.assertEqual('3/4',self.run_gate()['score_exact'])
    def test_missing_fails_coverage_even_when_score_ok(self):
        self.p['minimum_score']='1/2';self.rows.pop();self.assertIn('ENTERPRISE_COVERAGE_BELOW_THRESHOLD',self.run_gate()['reasons'])
    def test_blocked_score_not_credited(self):self.rows[0]['status']='BLOCKED';self.assertEqual('1/20',self.run_gate()['score_exact'])
    def test_empty_scores_fail(self):self.rows=[];self.assertEqual('0',self.run_gate()['score_exact'])
    def test_duplicate_score_rejects(self):
        self.rows.append(deepcopy(self.rows[0]))
        with self.assertRaisesRegex(BenchmarkError,'DUPLICATE_ROW'):self.run_gate()
    def test_unknown_metric_rejects(self):
        self.rows[0]['id']='unknown'
        with self.assertRaisesRegex(BenchmarkError,'UNEXPECTED_SCORE_ROW'):self.run_gate()
    def test_zero_weight_rejects(self):
        self.p['metrics'][0]['weight']='0'
        with self.assertRaises(BenchmarkError):self.run_gate()
    def test_score_boolean_negative_nonfinite_rejects(self):
        for value in [True,-1,float('nan'),'2']:
            self.rows[0]['score']=value
            with self.subTest(value=value),self.assertRaises(BenchmarkError):self.run_gate()
    def test_empty_metric_policy_rejects(self):
        self.p['metrics']=[]
        with self.assertRaises(BenchmarkError):self.run_gate()
    def test_policy_hash_rejects(self):
        with self.assertRaises(BenchmarkError):self.run_gate(pin='0'*64)
    def test_unknown_status_rejects(self):
        self.rows[0]['status']='PASS'
        with self.assertRaises(BenchmarkError):self.run_gate()
    def test_order_invariant(self):
        first=self.run_gate();self.rows.reverse();self.assertEqual(first,self.run_gate())
    def test_threshold_score_does_not_authorize_release(self):self.assertFalse(self.run_gate()['release_authorized'])
