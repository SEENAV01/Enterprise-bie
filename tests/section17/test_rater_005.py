import unittest
from copy import deepcopy
from batch005_helpers import ctx,ratings,rehash,aggregation_policy
from bie.evaluation.benchmarks.models import BenchmarkError,digest
from bie.evaluation.benchmarks.release.aggregation import aggregate
class AggregationRater005(unittest.TestCase):
    def setUp(self):self.ctx=ctx();self.rows=ratings(self.ctx);self.p=aggregation_policy()
    def run_aggregate(self,pin=None):return aggregate(self.ctx,self.rows,self.p,expected_policy_sha256=digest(self.p) if pin is None else pin)
    def test_positive_minimum(self):self.assertEqual('1',self.run_aggregate()['score_exact'])
    def test_conservative_minimum_not_mean(self):
        self.rows=ratings(self.ctx,('3/4','1'));self.assertEqual('3/4',self.run_aggregate()['score_exact'])
    def test_deterministic_zero_cannot_be_outvoted(self):self.rows=ratings(self.ctx,('0','1'));self.assertEqual('0',self.run_aggregate()['score_exact'])
    def test_missing_rater_zero_and_blocked(self):
        self.rows.pop();o=self.run_aggregate();self.assertEqual('0',o['score_exact']);self.assertEqual('BLOCKED',o['status'])
    def test_blocked_rater_zero_and_blocked(self):
        self.rows[1].update(status='BLOCKED',score_exact='0',reasons=['TIMEOUT']);rehash(self.rows[1]);self.assertIn('REQUIRED_RATER_BLOCKED',self.run_aggregate()['reasons'])
    def test_excess_disagreement_requires_adjudication(self):self.rows=ratings(self.ctx,('1/2','1'));self.assertIn('ADJUDICATION_REQUIRED',self.run_aggregate()['reasons'])
    def test_disagreement_boundary_exact(self):self.rows=ratings(self.ctx,('3/4','1'));self.assertEqual('MEASURED',self.run_aggregate()['status'])
    def test_duplicate_rater_rejects(self):
        self.rows.append(deepcopy(self.rows[0]))
        with self.assertRaisesRegex(BenchmarkError,'DUPLICATE_ASSESSMENT'):self.run_aggregate()
    def test_independence_group_clones_reject(self):
        self.p['raters'][1]['independence_group']=self.p['raters'][0]['independence_group']
        with self.assertRaisesRegex(BenchmarkError,'INDEPENDENCE_GROUP'):self.run_aggregate()
    def test_model_only_roster_rejects(self):
        self.p['raters'][0]['kind']='MODEL'
        with self.assertRaisesRegex(BenchmarkError,'DETERMINISTIC_RATER_REQUIRED'):self.run_aggregate()
    def test_unknown_assessor_rejects(self):
        self.rows[0]['assessor_id']='unknown';rehash(self.rows[0])
        with self.assertRaisesRegex(BenchmarkError,'UNEXPECTED_RATER'):self.run_aggregate()
    def test_wrong_kind_rejects(self):
        self.rows[0]['kind']='HUMAN';rehash(self.rows[0])
        with self.assertRaisesRegex(BenchmarkError,'UNEXPECTED_RATER'):self.run_aggregate()
    def test_policy_digest_cannot_be_changed(self):
        with self.assertRaisesRegex(BenchmarkError,'SNAPSHOT_MISMATCH'):self.run_aggregate(pin='0'*64)
    def test_candidate_binding_changed_rejects(self):
        self.rows[1]['context']['candidate_sha256']=digest('changed');rehash(self.rows[1])
        with self.assertRaisesRegex(BenchmarkError,'CONTEXT_MISMATCH'):self.run_aggregate()
    def test_all_missing_blocked(self):self.rows=[];self.assertEqual('BLOCKED',self.run_aggregate()['status'])
    def test_stable_result_order(self):
        a=self.run_aggregate();self.rows.reverse();self.assertEqual(a,self.run_aggregate())
    def test_score_aggregation_does_not_authorize_release(self):self.assertFalse(self.run_aggregate()['release_authorized'])
    def test_aggregate_has_integrity_hash(self):
        o=self.run_aggregate();self.assertEqual(digest({k:v for k,v in o.items() if k!='aggregate_sha256'}),o['aggregate_sha256'])
