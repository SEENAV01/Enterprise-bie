import unittest
from copy import deepcopy
from bie.evaluation.benchmarks.models import BenchmarkError,digest
from bie.evaluation.benchmarks.release.floors import evaluate
class HardFloors002(unittest.TestCase):
    def setUp(self):
        self.p={'id':'hard-floors','floors':[{'id':'source','minimum':'1'},{'id':'render','minimum':'9/10'}]}
        self.rows=[{'id':'source','status':'MEASURED','score':'1'},{'id':'render','status':'MEASURED','score':'9/10'}]
    def run_gate(self,pin=None):return evaluate(self.p,self.rows,expected_policy_sha256=digest(self.p) if pin is None else pin)
    def test_exact_boundary_passes(self):self.assertEqual('PASS',self.run_gate()['outcome'])
    def test_any_floor_fails_gate(self):self.rows[0]['score']='999/1000';self.assertEqual('FAIL',self.run_gate()['outcome'])
    def test_one_strong_metric_cannot_mask_other(self):self.rows[0]['score']='1/2';self.rows[1]['score']='1';self.assertEqual('FAIL',self.run_gate()['outcome'])
    def test_missing_critical_is_not_measured(self):self.rows.pop();self.assertIn('CRITICAL_METRIC_NOT_MEASURED',self.run_gate()['reasons'])
    def test_blocked_critical_cannot_claim_one(self):self.rows[0]['status']='BLOCKED';self.assertEqual('FAIL',self.run_gate()['outcome'])
    def test_zero_floor_still_requires_measured(self):self.p['floors'][0]['minimum']='0';self.rows=self.rows[1:];self.assertEqual('FAIL',self.run_gate()['outcome'])
    def test_all_missing_reports_every_failure(self):self.rows=[];self.assertEqual(2,len(self.run_gate()['failures']))
    def test_extra_metric_rejects(self):
        self.rows.append({'id':'unrelated','score':'1','status':'MEASURED'})
        with self.assertRaises(BenchmarkError):self.run_gate()
    def test_duplicate_floor_rejects(self):
        self.p['floors'].append(deepcopy(self.p['floors'][0]))
        with self.assertRaises(BenchmarkError):self.run_gate()
    def test_duplicate_result_rejects(self):
        self.rows.append(deepcopy(self.rows[0]))
        with self.assertRaises(BenchmarkError):self.run_gate()
    def test_invalid_floor_range_rejects(self):
        self.p['floors'][0]['minimum']='2'
        with self.assertRaises(BenchmarkError):self.run_gate()
    def test_empty_floor_policy_rejects(self):
        self.p['floors']=[]
        with self.assertRaises(BenchmarkError):self.run_gate()
    def test_hash_pin_rejects(self):
        with self.assertRaises(BenchmarkError):self.run_gate(pin='0'*64)
    def test_hard_floor_failures_deterministic(self):
        self.rows=[];a=self.run_gate();self.p['floors'].reverse();b=self.run_gate();self.assertEqual(a['failures'],b['failures'])
