from copy import deepcopy
import unittest
from batch005_helpers import regression_fixture
from bie.evaluation.benchmarks.models import BenchmarkError,digest
from bie.evaluation.benchmarks.metrics.regression import evaluate
class RegressionMetric017(unittest.TestCase):
    def setUp(self):self.r,self.c=regression_fixture()
    def run_metric(self,**kw):
        return evaluate(self.r,self.c,expected_reference_sha256=kw.pop('reference_sha',digest(self.r)),expected_candidate_sha256=kw.pop('candidate_sha',digest(self.c)),evaluator_id='det',**kw)
    def test_positive_exact_pair(self):self.assertEqual('1',self.run_metric()['score_exact'])
    def test_no_statistical_significance_claim(self):self.assertFalse(self.run_metric()['details']['statistical_significance_claimed'])
    def test_missing_case_remains_denominator(self):
        self.c['cases'].pop();o=self.run_metric();self.assertEqual('1/3',o['score_exact']);self.assertEqual(2,o['unit_count'])
    def test_critical_case_drop_not_hidden(self):
        self.c['cases'][0]['score']='99/100';self.assertEqual('FAIL',self.run_metric()['outcome'])
    def test_exact_tolerance_boundary(self):self.c['cases'][1]['score']='7/10';self.assertEqual('PASS',self.run_metric()['outcome'])
    def test_drop_below_boundary(self):self.c['cases'][1]['score']='699/1000';self.assertEqual('1/3',self.run_metric()['score_exact'])
    def test_blocked_case_cannot_claim_full_credit(self):self.c['cases'][0]['status']='BLOCKED';self.assertEqual('2/3',self.run_metric()['score_exact'])
    def test_skipped_is_failure(self):self.c['cases'][0]['status']='SKIPPED';self.assertEqual('FAIL',self.run_metric()['outcome'])
    def test_extra_case_is_rejected(self):
        self.c['cases'].append({**self.c['cases'][0],'id':'extra'})
        with self.assertRaisesRegex(BenchmarkError,'UNEXPECTED_REGRESSION_CASE'):self.run_metric()
    def test_duplicate_case_is_rejected(self):
        self.c['cases'].append(deepcopy(self.c['cases'][0]))
        with self.assertRaisesRegex(BenchmarkError,'DUPLICATE_ROW'):self.run_metric()
    def test_dataset_environment_code_changes_block(self):
        for k in ['dataset_sha256','environment_sha256','evaluator_sha256']:
            with self.subTest(k=k):
                old=self.c[k];self.c[k]=digest('changed')
                with self.assertRaisesRegex(BenchmarkError,'INCOMPARABLE_REGRESSION_CONTEXT'):self.run_metric()
                self.c[k]=old
    def test_changed_case_digest_blocked(self):
        self.c['cases'][0]['case_sha256']=digest('other')
        with self.assertRaisesRegex(BenchmarkError,'REGRESSION_CASE_CHANGED'):self.run_metric()
    def test_relabel_metric_blocked(self):
        self.c['cases'][0]['metric_id']='BIE-EVAL-METRIC-003'
        with self.assertRaisesRegex(BenchmarkError,'REGRESSION_CASE_CHANGED'):self.run_metric()
    def test_baseline_run_cannot_be_reused(self):
        self.c['run_id']='old'
        with self.assertRaisesRegex(BenchmarkError,'BASELINE_REUSED'):self.run_metric()
    def test_bad_score_types_and_range(self):
        for value in [True,-1,'2','NaN']:
            self.c['cases'][0]['score']=value
            with self.subTest(value=value),self.assertRaises(BenchmarkError):self.run_metric()
    def test_empty_reference_blocked(self):
        self.r['payload']['cases']=[]
        with self.assertRaises(BenchmarkError):self.run_metric()
    def test_hash_pins_enforced(self):
        for k in ['reference_sha','candidate_sha']:
            with self.subTest(k=k),self.assertRaises(BenchmarkError):self.run_metric(**{k:'0'*64})
    def test_candidate_pass_flag_rejected(self):
        self.c['pass']=True
        with self.assertRaises(BenchmarkError):self.run_metric()
    def test_no_release_promotion(self):self.assertFalse(self.run_metric()['release_authorized']);self.assertFalse(self.run_metric()['product_accepted'])
    def test_order_independent(self):
        first=self.run_metric();self.c['cases'].reverse();self.r['payload']['cases'].reverse();second=self.run_metric()
        self.assertEqual(first['units'],second['units']);self.assertEqual(first['details'],second['details'])
