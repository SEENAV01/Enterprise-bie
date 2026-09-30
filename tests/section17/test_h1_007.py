import unittest
from copy import deepcopy
from pathlib import Path
import tempfile
from unittest.mock import patch
from bie.evaluation.benchmarks.models import BenchmarkError, digest, canonical_json, strict_loads

from h1_helpers import production_fixture,gate_fixture_args,sign_h1
from bie.evaluation.benchmarks.release.admission import verify_admission
from bie.evaluation.benchmarks.release import gate
from batch005_helpers import NOW,rehash
class AssessmentCustodyBoundary(unittest.TestCase):
    def setUp(self):self.m,self.p,self.rows,self.b,self.c,self.tr,self.tokens=production_fixture()
    def admit(self):return verify_admission(self.rows,self.p,self.tokens,self.tr,now=NOW)
    def test_correct_service_signatures_verify(self):self.assertEqual(68,len(self.admit()['records']))
    def test_missing_one_signature_rejects(self):
        self.tokens.pop()
        with self.assertRaisesRegex(BenchmarkError,'MISSING_ASSESSMENT'):self.admit()
    def test_duplicate_signature_rejects(self):
        self.tokens.append(self.tokens[0])
        with self.assertRaisesRegex(BenchmarkError,'DUPLICATE_ASSESSMENT_AUTHORIZATION'):self.admit()
    def test_rehashed_score_cannot_reuse_signature(self):
        self.rows[0]['score_exact']='0';rehash(self.rows[0])
        with self.assertRaises(BenchmarkError):self.admit()
    def test_revoked_service_rejects(self):
        self.tr['det']['revoked']=True
        with self.assertRaisesRegex(BenchmarkError,'UNAUTHORIZED_ATTESTOR'):self.admit()
    def test_fixture_key_rejects(self):
        self.tr['det']['fixture_only']=True
        with self.assertRaisesRegex(BenchmarkError,'FIXTURE_KEY'):self.admit()
    def test_fixture_execution_rejects(self):
        self.rows[0]['execution']='FIXTURE';rehash(self.rows[0])
        a=self.rows[0];self.tokens[0]=sign_h1(self.tr,'det','EVALUATOR_ASSESSMENT',a['assessment_sha256'],{'assessment_sha256':a['assessment_sha256'],'kind':a['kind'],'assessor_version':a['assessor_version'],'independence_group':'code-author'})
        with self.assertRaisesRegex(BenchmarkError,'EXECUTION_NOT_PRODUCTION'):self.admit()
    def test_wrong_role_rejects(self):
        self.tr['det']['roles']=['POLICY_APPROVAL']
        with self.assertRaises(BenchmarkError):self.admit()
    def test_shared_secrets_do_not_fake_independence(self):
        self.tr['human']['secret']=self.tr['det']['secret']
        for i,t in enumerate(self.tokens):
            p=t['payload'];self.tokens[i]=sign_h1(self.tr,p['key_id'],p['kind'],p['scope_sha256'],p['claims'])
        with self.assertRaisesRegex(BenchmarkError,'KEY_REUSED'):self.admit()
    def test_false_version_claim_rejects(self):
        p=self.tokens[0]['payload'];claims=deepcopy(p['claims']);claims['assessor_version']='fake'
        self.tokens[0]=sign_h1(self.tr,p['key_id'],p['kind'],p['scope_sha256'],claims)
        with self.assertRaisesRegex(BenchmarkError,'CLAIMS_MISMATCH'):self.admit()
    def test_signature_bitflip_rejects(self):
        self.tokens[0]['signature']='0'*64
        with self.assertRaisesRegex(BenchmarkError,'BAD_ATTESTATION_SIGNATURE'):self.admit()
    def test_missing_all_signatures_blocks_public_production_gate(self):
        args=gate_fixture_args();args.pop('assessment_tokens');o=gate.evaluate(**args)
        self.assertEqual('BLOCKED',o['outcome']);self.assertIn('MISSING_ASSESSMENT_AUTHORIZATION',o['reasons'])
    def test_independent_accuracy_not_inferred(self):self.assertFalse(self.admit()['scientific_accuracy_certified'])
