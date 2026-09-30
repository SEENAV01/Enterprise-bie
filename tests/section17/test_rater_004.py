import unittest
from copy import deepcopy
from batch005_helpers import ctx,ratings,rehash
from bie.evaluation.benchmarks.models import BenchmarkError
from bie.evaluation.benchmarks.release.agreement import evaluate
class AgreementRater004(unittest.TestCase):
    def setUp(self):
        self.contexts=[ctx(case=f'case{i}') for i in range(4)]
        self.rows=[a for c,v in zip(self.contexts,[('1','1'),('1','0'),('0','1'),('0','0')]) for a in ratings(c,v)]
    def run_agreement(self,**kw):return evaluate(self.contexts,self.rows,assessor_ids=kw.pop('raters',['det','human']),**kw)
    def test_balanced_independent_labels_kappa_zero(self):
        p=self.run_agreement()['pairs'][0];self.assertEqual('1/2',p['observed_agreement']);self.assertEqual('0',p['kappa'])
    def test_perfect_non_degenerate_agreement(self):
        for i in range(0,len(self.rows),2):self.rows[i+1]['score_exact']=self.rows[i]['score_exact'];rehash(self.rows[i+1])
        self.assertEqual('1',self.run_agreement()['pairs'][0]['kappa'])
    def test_complete_disagreement_negative_kappa(self):
        for i in range(0,len(self.rows),2):self.rows[i+1]['score_exact']='0' if self.rows[i]['score_exact']=='1' else '1';rehash(self.rows[i+1])
        self.assertEqual('-1',self.run_agreement()['pairs'][0]['kappa'])
    def test_degenerate_kappa_explicitly_undefined(self):
        for row in self.rows:row['score_exact']='1';rehash(row)
        p=self.run_agreement()['pairs'][0];self.assertIsNone(p['kappa']);self.assertEqual('UNDEFINED',p['kappa_state'])
    def test_missing_not_dropped_into_complete_report(self):
        self.rows.pop();o=self.run_agreement();self.assertEqual('BLOCKED',o['status']);self.assertEqual(4,o['pairs'][0]['expected_count']);self.assertEqual(3,o['pairs'][0]['paired_count'])
    def test_all_missing_has_no_fake_agreement(self):self.rows=[];self.assertIsNone(self.run_agreement()['pairs'][0]['observed_agreement'])
    def test_blocked_assessor_reduces_pairs(self):
        self.rows[0].update(status='BLOCKED',score_exact='0',reasons=['ERROR']);rehash(self.rows[0]);self.assertEqual(3,self.run_agreement()['pairs'][0]['paired_count'])
    def test_duplicate_rater_per_case_rejects(self):
        self.rows.append(deepcopy(self.rows[0]))
        with self.assertRaisesRegex(BenchmarkError,'DUPLICATE_ASSESSMENT'):self.run_agreement()
    def test_unknown_case_rejects(self):
        self.rows[0]['context']['case_id']='unknown';rehash(self.rows[0])
        with self.assertRaisesRegex(BenchmarkError,'UNEXPECTED_ASSESSMENT'):self.run_agreement()
    def test_context_changed_rejects(self):
        self.rows[0]['context']['run_id']='different';rehash(self.rows[0])
        with self.assertRaisesRegex(BenchmarkError,'CONTEXT_MISMATCH'):self.run_agreement()
    def test_rater_roster_requires_two(self):
        with self.assertRaises(BenchmarkError):self.run_agreement(raters=['det'])
    def test_sample_too_small_rejects(self):
        with self.assertRaisesRegex(BenchmarkError,'SAMPLE_TOO_SMALL'):self.run_agreement(minimum_pairs=5)
    def test_mae_computed_exactly(self):self.assertEqual('1/2',self.run_agreement()['pairs'][0]['mean_absolute_score_difference'])
    def test_duplicate_context_rejects(self):
        self.contexts.append(deepcopy(self.contexts[0]))
        with self.assertRaisesRegex(BenchmarkError,'DUPLICATE_CASE_CONTEXT'):self.run_agreement()
    def test_order_independent(self):
        a=self.run_agreement();self.contexts.reverse();self.rows.reverse();self.assertEqual(a,self.run_agreement())
    def test_no_accuracy_inference(self):self.assertFalse(self.run_agreement()['accuracy_inferred'])
    def test_invalid_threshold_rejects(self):
        with self.assertRaises(BenchmarkError):self.run_agreement(pass_threshold='2')
    def test_false_json_acceptance_rejects(self):
        self.rows[0]['product_accepted']=True;rehash(self.rows[0])
        with self.assertRaisesRegex(BenchmarkError,'UNAUTHORIZED_PROMOTION'):self.run_agreement()
