import unittest
from copy import deepcopy
from batch005_helpers import ctx,metric_fixture,regression_fixture
from bie.evaluation.benchmarks.models import BenchmarkError,digest
from bie.evaluation.benchmarks.release import deterministic as d
from bie.evaluation.benchmarks.release.contracts import assessment
class DeterministicRater001(unittest.TestCase):
    def setUp(self):
        self.r,self.c,self.a=metric_fixture();self.ctx=ctx(reference=self.r,candidate=self.c)
    def execute(self,**kw):return d.execute(self.ctx,self.r,self.c,expected_code_sha256=kw.pop('code',d.service_code_sha256()),source_artifacts=self.a,**kw)
    def test_known_metric_actually_runs(self):self.assertEqual('1',self.execute()['score_exact'])
    def test_all_seventeen_routes(self):self.assertEqual(17,len(d.IMPLEMENTED_METRICS))
    def test_legacy_router_snapshot_remains_sixteen(self):
        from bie.evaluation.benchmarks.metrics import ALL_MODULES
        self.assertEqual(16,len(ALL_MODULES))
    def test_regression_route(self):
        self.r,self.c=regression_fixture();self.a={};self.ctx=ctx(metric='BIE-EVAL-METRIC-017',reference=self.r,candidate=self.c)
        self.assertEqual('1',self.execute()['score_exact'])
    def test_changed_code_pin_rejected(self):
        with self.assertRaisesRegex(BenchmarkError,'EVALUATOR_CODE_CHANGED'):self.execute(code='0'*64)
    def test_candidate_hash_rejected(self):
        self.ctx['candidate_sha256']='0'*64
        with self.assertRaises(BenchmarkError):self.execute()
    def test_reference_hash_rejected(self):
        self.ctx['reference_sha256']='0'*64
        with self.assertRaises(BenchmarkError):self.execute()
    def test_rubric_hash_rejected(self):
        self.ctx['rubric_sha256']='0'*64
        with self.assertRaises(BenchmarkError):self.execute()
    def test_separate_pinned_rubric_supported(self):
        rubric={'id':'independent-scoring'};self.ctx['rubric_sha256']=digest(rubric)
        self.assertEqual('1',self.execute(rubric=rubric)['score_exact'])
    def test_unknown_metric_rejected(self):
        self.ctx['metric_id']='BIE-EVAL-METRIC-999'
        with self.assertRaises(BenchmarkError):self.execute()
    def test_candidate_schema_invalid_becomes_blocked(self):
        self.c['passed']=True;self.ctx['candidate_sha256']=digest(self.c)
        self.assertEqual('BLOCKED',self.execute()['status'])
    def test_missing_compile_observation_blocked(self):
        self.r,self.c,_=metric_fixture(11);self.a={};self.ctx=ctx(metric='BIE-EVAL-METRIC-011',reference=self.r,candidate=self.c)
        self.assertEqual('BLOCKED',self.execute()['status'])
    def test_actual_metric_receipt_digest(self):
        o=self.execute();self.assertEqual(digest(o['evidence']['metric_result']),o['evidence']['metric_result_sha256'])
    def test_assessment_integrity(self):self.assertEqual(self.execute(),assessment(self.execute(),self.ctx))
    def test_modified_score_detected(self):
        o=self.execute();o['score_exact']='0'
        with self.assertRaisesRegex(BenchmarkError,'ASSESSMENT_INTEGRITY'):assessment(o)
    def test_execution_is_not_product_acceptance(self):o=self.execute();self.assertFalse(o['product_accepted']);self.assertFalse(o['release_authorized'])
    def test_deterministic_results_repeat(self):self.assertEqual(self.execute(),self.execute())
    def test_input_not_mutated(self):
        before=deepcopy((self.ctx,self.r,self.c,self.a));self.execute();self.assertEqual(before,(self.ctx,self.r,self.c,self.a))
