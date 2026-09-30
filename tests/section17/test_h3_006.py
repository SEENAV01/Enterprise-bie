import unittest,tempfile,shutil,json,hashlib,os
from pathlib import Path
from copy import deepcopy
from dataclasses import asdict,replace
from unittest.mock import patch
from bie.evaluation.benchmarks.models import BenchmarkError,digest,canonical_json
from bie.evaluation.benchmarks.adoption.contracts import *
from h3_support import fixture,measure,measured,rater,context,TD,LIMITS,ROOT,media,sha,policy,report,CONTRACT

from bie.evaluation.benchmarks.release.deterministic import evaluate_metric,service_code_sha256
from bie.evaluation.benchmarks.metrics import evaluate as api
from batch005_helpers import metric_fixture
class ExistingRaterAdoptionTests(unittest.TestCase):
    def test_existing_metric_api_executes_versioned_av(self):self.assertEqual('av-adoption-3',measured()['metric_profile'])
    def test_existing_rater_creates_bound_assessment(self):
        a=rater();self.assertEqual('MEASURED',a['status']);self.assertEqual('1',a['score_exact']);self.assertEqual('av-adoption-3',a['evidence']['metric_result']['metric_profile'])
    def test_rater_wrong_media_is_measured_failure(self):
        ref,c=fixture();ref['av_policy']['expected_frames']=20;a=rater(ref=ref,candidate=c);self.assertEqual('MEASURED',a['status']);self.assertEqual('0',a['score_exact'])
    def test_rater_missing_context_is_blocked(self):
        a=rater(execution_context=None);self.assertEqual('BLOCKED',a['status']);self.assertIn('TRUSTED_AV_EXECUTION_CONTEXT_REQUIRED',a['reasons'])
    def test_rater_code_pin_mismatch_before_decode(self):
        with self.assertRaisesRegex(BenchmarkError,'EVALUATOR_CODE_CHANGED'):rater(expected_code_sha256='0'*64)
    def test_rater_missing_media_is_blocked(self):
        ref,c=fixture();c['media']['path']='missing.mkv';a=rater(ref=ref,candidate=c);self.assertEqual('BLOCKED',a['status'])
    def test_legacy_metric_remains_available(self):
        ref,c,a=metric_fixture(7);v=api(ref['metric_id'],ref,c,expected_reference_sha256=digest(ref),expected_candidate_sha256=digest(c),source_artifacts=a);self.assertEqual('PASS',v['outcome']);self.assertNotIn('metric_profile',v)
    def test_cannot_silently_mix_legacy_context(self):
        ref,c,a=metric_fixture(7)
        with self.assertRaisesRegex(BenchmarkError,'UNUSED_AV_EXECUTION_CONTEXT'):api(ref['metric_id'],ref,c,expected_reference_sha256=digest(ref),expected_candidate_sha256=digest(c),source_artifacts=a,execution_context=ExecutionContext(TD,LIMITS))
    def test_unknown_av_profile_schema_not_downgraded(self):
        ref,c=fixture();ref['schema_version']='metric-av-reference-4'
        with self.assertRaises(BenchmarkError):measure(ref=ref,candidate=c)
    def test_provider_exception_redacted_and_blocked(self):
        with patch('bie.evaluation.benchmarks.adoption.metric.service.collect_and_evaluate',side_effect=RuntimeError('SECRET_DATA')):a=rater()
        self.assertEqual('BLOCKED',a['status']);self.assertNotIn('SECRET_DATA',canonical_json(a))
    def test_full_evaluator_hash_includes_adoption(self):
        m=measured();self.assertEqual(service_code_sha256(),m['evaluator_code_sha256'])
    def test_injected_receipt_is_blocked_by_rater(self):
        a=rater(source_artifacts={'receipt':{'status':'PASS'}});self.assertEqual('BLOCKED',a['status']);self.assertIn('AV_RECEIPT_INJECTION_REJECTED',a['reasons'])

    def test_decoder_failure_receipt_retained_by_rater(self):
        p=media('corrupt');ref,c=fixture();c['media']={'path':p.name,'sha256':sha(p),'size_bytes':p.stat().st_size}
        a=rater(ref=ref,candidate=c,execution_context=ExecutionContext(p.parent,LIMITS))
        self.assertEqual('BLOCKED',a['status']);self.assertEqual('BLOCKED',a['evidence']['av_collection']['status'])
