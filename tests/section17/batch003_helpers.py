"""Batch003 independent expected fixtures and candidate-bound metric test helpers."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from bie.evaluation.benchmarks.models import BenchmarkError,digest
from bie.evaluation.benchmarks.metrics import evaluate
from batch002_helpers import Batch002Base,attach_fixture_tests,q
ROOT=Path(__file__).resolve().parents[2]
class MetricBase(unittest.TestCase):
    task=None
    def fixture(self):
        return json.loads((ROOT/'bie/evaluation/benchmarks/metrics/fixtures'/f'{self.task}.json').read_text())
    def example(self,index=0):
        f=self.fixture();return f['reference'],f['cases'][index]['candidate'],f['source_artifacts']
    def measure(self,reference=None,candidate=None,artifacts=None):
        r,c,a=self.example()
        r=r if reference is None else reference;c=c if candidate is None else candidate;a=a if artifacts is None else artifacts
        return evaluate(self.task,r,c,expected_reference_sha256=digest(r),expected_candidate_sha256=digest(c),source_artifacts=a)
    def reject(self,reference=None,candidate=None,artifacts=None,code=None):
        with self.assertRaises(BenchmarkError) as ctx:self.measure(reference,candidate,artifacts)
        if code:self.assertEqual(code,ctx.exception.code)
        return ctx.exception.code
    def reasons(self,out):return {d['reason'] for d in out['defects']}
def attach_metric_fixtures(cls):
    for index in range(6):
        def test(self,index=index):
            fixture=self.fixture();case=fixture['cases'][index]
            out=self.measure(fixture['reference'],case['candidate'],fixture['source_artifacts'])
            self.assertEqual(case['expected_outcome'],out['outcome'],out)
            self.assertEqual(case['expected_score_exact'],out['score_exact'],out)
            if case['expected_reason']:self.assertIn(case['expected_reason'],self.reasons(out))
            self.assertEqual('AUTHORED_DIAGNOSTIC',out['evidence_grade']);self.assertFalse(out['release_authorized'])
        setattr(cls,f'test_authored_candidate_{index+1:03d}',test)
    return cls

# Bounded floating-point profiles compare through the explicit case tolerances.
# Exact rational strings, dictionary structure and rejection codes remain exact.
def attach_fixture_tests(cls):
    from bie.evaluation.benchmarks.runner import load_pack,reference_output,grade_case
    for index in range(12):
        def test(self,index=index):
            case=load_pack(self.task)[index]
            out=reference_output(self.task,case.inputs)
            report=grade_case(case,out)
            self.assertEqual('PASS',report['status'],report)
            self.assertEqual('DEVELOPMENT',case.split)
            self.assertEqual('AUTHORED_DIAGNOSTIC',case.evidence_grade)
            self.assertFalse(report['release_authorized'])
        setattr(cls,f'test_authored_case_{index+1:03d}',test)
    return cls
