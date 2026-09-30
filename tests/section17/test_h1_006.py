import unittest
from copy import deepcopy
from pathlib import Path
import tempfile
from unittest.mock import patch
from bie.evaluation.benchmarks.models import BenchmarkError, digest, canonical_json, strict_loads

from h1_helpers import bundle_fixture,gate_fixture_args
from bie.evaluation.benchmarks.release.bundle import verify_bundle
from bie.evaluation.benchmarks.release import gate
class CandidateBundleBoundary(unittest.TestCase):
    def setUp(self):self.m,self.p,self.rows,self.b=bundle_fixture()
    def test_matching_bytes_verified(self):self.assertEqual(3,verify_bundle(self.m,self.b)['verified_cases'])
    def test_changed_candidate_rejected(self):
        self.b['candidates']['case1']={'new':1};self.m['artifact_sha256']=digest(self.b)
        with self.assertRaisesRegex(BenchmarkError,'CONTENT_MISMATCH'):verify_bundle(self.m,self.b)
    def test_unrelated_artifact_hash_rejected(self):
        self.m['artifact_sha256']=digest('unrelated')
        with self.assertRaisesRegex(BenchmarkError,'ARTIFACT_MISMATCH'):verify_bundle(self.m,self.b)
    def test_missing_case_rejected(self):
        self.b['candidates'].pop('case1')
        with self.assertRaisesRegex(BenchmarkError,'ROSTER_MISMATCH'):verify_bundle(self.m,self.b)
    def test_extra_case_rejected(self):
        self.b['candidates']['extra']=None
        with self.assertRaises(BenchmarkError):verify_bundle(self.m,self.b)
    def test_unknown_bundle_field_rejected(self):
        self.b['passed']=True
        with self.assertRaises(BenchmarkError):verify_bundle(self.m,self.b)
    def test_wrong_schema_rejected(self):
        self.b['schema_version']='9.0.0'
        with self.assertRaises(BenchmarkError):verify_bundle(self.m,self.b)
    def test_list_candidates_rejected(self):
        self.b['candidates']=[]
        with self.assertRaises(BenchmarkError):verify_bundle(self.m,self.b)
    def test_empty_manifest_denominator_rejected(self):
        self.m['cases']=[];self.b['candidates']={}
        with self.assertRaises(BenchmarkError):verify_bundle(self.m,self.b)
    def test_order_independent_dictionary(self):
        self.b['candidates']=dict(reversed(list(self.b['candidates'].items())))
        self.assertEqual(3,verify_bundle(self.m,self.b)['verified_cases'])
    def test_production_missing_bundle_is_blocked(self):
        args=gate_fixture_args();args.pop('candidate_bundle');o=gate.evaluate(**args)
        self.assertIn('MISSING_CANDIDATE_BUNDLE',o['reasons']);self.assertEqual('BLOCKED',o['outcome'])
    def test_structured_binding_not_native_claim(self):self.assertFalse(verify_bundle(self.m,self.b)['native_artifact_verified'])
