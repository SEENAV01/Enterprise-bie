import unittest
from copy import deepcopy
from pathlib import Path
import tempfile
from unittest.mock import patch
from bie.evaluation.benchmarks.models import BenchmarkError, digest, canonical_json, strict_loads

from batch005_helpers import metric_fixture,ctx
from bie.evaluation.benchmarks.release import deterministic as det
class DeterministicFaultBoundary(unittest.TestCase):
    def setUp(self):
        self.r,self.c,self.blobs=metric_fixture(7);self.ctx=ctx(reference=self.r,candidate=self.c);self.code=det.service_code_sha256()
    def run_det(self):return det.execute(self.ctx,self.r,self.c,expected_code_sha256=self.code,source_artifacts=self.blobs)
    def test_positive_still_measured(self):self.assertEqual('MEASURED',self.run_det()['status'])
    def test_runtime_exception_becomes_blocked(self):
        with patch.object(det,'evaluate_metric',side_effect=RuntimeError('secret-key')):o=self.run_det()
        self.assertEqual('BLOCKED',o['status']);self.assertEqual('0',o['score_exact'])
    def test_exception_text_not_in_receipt(self):
        with patch.object(det,'evaluate_metric',side_effect=ValueError('private-token-123')):o=self.run_det()
        self.assertNotIn('private-token-123',canonical_json(o))
    def test_type_fault_blocked(self):
        with patch.object(det,'evaluate_metric',side_effect=TypeError('private')):o=self.run_det()
        self.assertIn('DETERMINISTIC_EXECUTION_FAILED',o['reasons'])
    def test_arithmetic_fault_blocked(self):
        with patch.object(det,'evaluate_metric',side_effect=ZeroDivisionError()):o=self.run_det()
        self.assertEqual('BLOCKED',o['status'])
    def test_expected_contract_fault_retains_code(self):
        with patch.object(det,'evaluate_metric',side_effect=BenchmarkError('MY_TYPED_ERROR')):o=self.run_det()
        self.assertEqual(['MY_TYPED_ERROR'],o['reasons'])
    def test_code_pin_wrong_rejected_before_execution(self):
        self.code='0'*64
        with self.assertRaisesRegex(BenchmarkError,'EVALUATOR_CODE_CHANGED'): self.run_det()
    def test_code_changes_during_execution_blocked(self):
        with patch.object(det,'service_code_sha256',side_effect=[self.code,'0'*64]):o=self.run_det()
        self.assertIn('EVALUATOR_CODE_CHANGED_DURING_RUN',o['reasons'])
    def test_candidate_argument_not_mutated_by_faulty_evaluator(self):
        before=deepcopy(self.c)
        def mutate(metric,r,c,**kw):c['tampered']=True;raise BenchmarkError('MUTATOR')
        with patch.object(det,'evaluate_metric',side_effect=mutate):self.run_det()
        self.assertEqual(before,self.c)
    def test_reference_argument_not_mutated_by_faulty_evaluator(self):
        before=deepcopy(self.r)
        def mutate(metric,r,c,**kw):r['payload'].clear();raise BenchmarkError('MUTATOR')
        with patch.object(det,'evaluate_metric',side_effect=mutate):self.run_det()
        self.assertEqual(before,self.r)
    def test_bad_candidate_pin_not_coerced_to_score(self):
        self.c['unexpected']=1
        with self.assertRaisesRegex(BenchmarkError,'SNAPSHOT_MISMATCH'):self.run_det()
    def test_blocked_receipt_integrity(self):
        with patch.object(det,'evaluate_metric',side_effect=OverflowError()):o=self.run_det()
        self.assertEqual(o['assessment_sha256'],digest({k:v for k,v in o.items() if k!='assessment_sha256'}))

    def test_malformed_evaluator_result_blocked(self):
        with patch.object(det,'evaluate_metric',return_value={}):o=self.run_det()
        self.assertEqual('BLOCKED',o['status'])
    def test_overcredited_result_blocked(self):
        original=det.evaluate_metric
        def corrupt(*args,**kw):
            r=original(*args,**kw);r['score_exact']='2';return r
        with patch.object(det,'evaluate_metric',side_effect=corrupt):o=self.run_det()
        self.assertEqual('BLOCKED',o['status'])
    def test_result_for_other_candidate_blocked(self):
        original=det.evaluate_metric
        def corrupt(*args,**kw):
            r=original(*args,**kw);r['candidate_sha256']=digest('other');return r
        with patch.object(det,'evaluate_metric',side_effect=corrupt):o=self.run_det()
        self.assertEqual('BLOCKED',o['status'])
    def test_result_score_recomputed_from_units(self):
        original=det.evaluate_metric
        def corrupt(*args,**kw):
            r=original(*args,**kw);r['units'][0]['credit']='0';return r
        with patch.object(det,'evaluate_metric',side_effect=corrupt):o=self.run_det()
        self.assertEqual('BLOCKED',o['status'])

    def test_missing_defects_cannot_escape_receipt_boundary(self):
        original=det.evaluate_metric
        def corrupt(*args,**kw):
            r=original(*args,**kw);r.pop('defects');return r
        with patch.object(det,'evaluate_metric',side_effect=corrupt):o=self.run_det()
        self.assertEqual('BLOCKED',o['status'])
    def test_malformed_defect_reason_blocked(self):
        original=det.evaluate_metric
        def corrupt(*args,**kw):
            r=original(*args,**kw);r['defects']=[{'reason':{'secret':'not a reason'}}];return r
        with patch.object(det,'evaluate_metric',side_effect=corrupt):o=self.run_det()
        self.assertEqual('BLOCKED',o['status'])
