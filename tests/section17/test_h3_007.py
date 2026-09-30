import unittest,tempfile,shutil,json,hashlib,os,subprocess,sys
from pathlib import Path
from copy import deepcopy
from dataclasses import asdict,replace
from unittest.mock import patch
from bie.evaluation.benchmarks.models import BenchmarkError,digest,canonical_json
from bie.evaluation.benchmarks.adoption.contracts import *
from h3_support import *

from bie.evaluation.benchmarks.adoption.native import inspect,authorize,verify_manifest
class NativeLineageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.av,self.path,self.exp=native_workspace(self.root)
    def tearDown(self):self.tmp.cleanup()
    def inspect(self):return inspect(self.root,self.path,self.av,expectation=self.exp,expected_expectation_sha256=digest(self.exp),contract_path=CONTRACT)
    def token(self,lineage):return token('NATIVE_AV_COLLECTION',lineage['lineage_sha256'],{'execution_kind':'LOCAL_REMOTION_CLI','lineage_sha256':lineage['lineage_sha256']})
    def test_actual_manifest_bytes_verified_not_native_execution(self):
        r=self.inspect();self.assertEqual('CUSTODY_VERIFIED_UNSIGNED',r['status']);self.assertFalse(r['native_execution_verified']);self.assertFalse(r['worker_authorized']);self.assertEqual(4,r['source_check']['files_checked'])
    def test_changed_source_bytes_fail(self):
        (self.root/'src/index.tsx').write_text('changed')
        with self.assertRaises(BenchmarkError):self.inspect()
    def test_missing_required_source_path_fails(self):
        self.exp['required_source_paths'].append('src/missing.tsx')
        with self.assertRaisesRegex(BenchmarkError,'NATIVE_SOURCE_COVERAGE_MISSING'):self.inspect()
    def test_changed_render_output_fails(self):
        (self.root/'out/lesson.mp4').write_bytes(b'bad')
        with self.assertRaises(BenchmarkError):self.inspect()
    def test_missing_artifact_seal_fails(self):
        (self.root/'render-evidence/native_fixture/ARTIFACT_MANIFEST.json').unlink()
        with self.assertRaises(BenchmarkError):self.inspect()
    def test_changed_sealed_process_evidence_fails(self):
        json_file(self.root,'render-evidence/native_fixture/render-process.json',{'passed':True})
        with self.assertRaises(BenchmarkError):self.inspect()
    def test_manifest_cannot_include_itself(self):
        base='render-evidence/native_fixture/ARTIFACT_MANIFEST.json';v=json.loads((self.root/base).read_text());v['artifacts'].append({'path':base,'size_bytes':0,'sha256':sha(self.root/base)});v['artifacts']=sorted(v['artifacts'],key=lambda a:a['path']);v['manifest_sha256']=digest({k:x for k,x in v.items() if k!='manifest_sha256'});json_file(self.root,base,v);self.exp['artifact_manifest_sha256']=v['manifest_sha256']
        with self.assertRaisesRegex(BenchmarkError,'NATIVE_MANIFEST_PATHS'):self.inspect()
    def test_missing_pinned_seal_coverage_fails_even_when_rehashed(self):
        base='render-evidence/native_fixture/ARTIFACT_MANIFEST.json';v=json.loads((self.root/base).read_text());v['artifacts']=[x for x in v['artifacts'] if not x['path'].endswith('isolation.json')];v['manifest_sha256']=digest({k:x for k,x in v.items() if k!='manifest_sha256'});json_file(self.root,base,v);self.exp['artifact_manifest_sha256']=v['manifest_sha256']
        with self.assertRaisesRegex(BenchmarkError,'NATIVE_SEAL_COVERAGE_MISSING'):self.inspect()
    def test_smoke_receipt_rejected(self):
        n=json.loads((self.root/self.path).read_text());n['mode']='smoke';json_file(self.root,self.path,n)
        with self.assertRaisesRegex(BenchmarkError,'NATIVE_PARTIAL_RENDER_REJECTED'):self.inspect()
    def test_injected_runner_rejected(self):
        n=json.loads((self.root/self.path).read_text());n['execution_kind']='INJECTED_TEST_RUNNER';json_file(self.root,self.path,n)
        with self.assertRaisesRegex(BenchmarkError,'NATIVE_FIXTURE_EXECUTION_REJECTED'):self.inspect()
    def test_wrong_recipe_pin_rejected(self):
        self.exp['recipe_sha256']='c'*64
        with self.assertRaises(BenchmarkError):self.inspect()
    def test_wrong_scene_binding_rejected(self):
        self.exp['scene_sha256']='c'*64
        with self.assertRaisesRegex(BenchmarkError,'NATIVE_RECIPE_SOURCE_MISMATCH'):self.inspect()
    def test_wrong_commit_requires_rebase(self):
        self.exp['commit']='c'*40
        with self.assertRaisesRegex(BenchmarkError,'NATIVE_CONTRACT_DRIFT'):self.inspect()
    def test_symlink_in_source_manifest_rejected(self):
        p=self.root/'src/index.tsx';b=p.read_bytes();p.unlink();(self.root/'replacement').write_bytes(b);p.symlink_to(self.root/'replacement')
        with self.assertRaises(BenchmarkError):self.inspect()
    def test_hard_link_does_not_invalidate_unchanged_bytes(self):
        source=self.root/'out/lesson.mp4';os.link(source,self.root/'same.mp4');self.assertEqual('CUSTODY_VERIFIED_UNSIGNED',self.inspect()['status'])
    def test_fixture_key_only_diagnostic_authority(self):
        r=self.inspect();a=authorize(r,self.token(r),trust(roles=['NATIVE_AV_COLLECTION']),now=NOW,production=False)
        self.assertEqual('AUTHORIZED_WORKER_ASSERTION',a['status']);self.assertFalse(a['production_key_policy']);self.assertFalse(a['native_execution_verified'])
    def test_fixture_key_rejected_in_production(self):
        r=self.inspect()
        with self.assertRaisesRegex(BenchmarkError,'FIXTURE_KEY_NOT_PRODUCTION'):authorize(r,self.token(r),trust(roles=['NATIVE_AV_COLLECTION']),now=NOW,production=True)
    def test_expired_attestation_rejected(self):
        r=self.inspect()
        with self.assertRaises(BenchmarkError):authorize(r,self.token(r),trust(roles=['NATIVE_AV_COLLECTION']),now=3000,production=False)
    def test_wrong_worker_role_rejected(self):
        r=self.inspect()
        with self.assertRaisesRegex(BenchmarkError,'UNAUTHORIZED_ATTESTOR'):authorize(r,self.token(r),trust(),now=NOW,production=False)
    def test_revoked_worker_rejected(self):
        r=self.inspect();t=trust(roles=['NATIVE_AV_COLLECTION']);t['test-key']['revoked']=True
        with self.assertRaises(BenchmarkError):authorize(r,self.token(r),t,now=NOW,production=False)
    def test_changed_lineage_cannot_reuse_signature(self):
        r=self.inspect();t=self.token(r);r['run_id']='changed';r['lineage_sha256']=digest({k:v for k,v in r.items() if k!='lineage_sha256'})
        with self.assertRaisesRegex(BenchmarkError,'ATTESTATION_SCOPE_MISMATCH'):authorize(r,t,trust(roles=['NATIVE_AV_COLLECTION']),now=NOW,production=False)
    def test_bad_signature_rejected(self):
        r=self.inspect();t=self.token(r);t['signature']='0'*64
        with self.assertRaisesRegex(BenchmarkError,'BAD_ATTESTATION_SIGNATURE'):authorize(r,t,trust(roles=['NATIVE_AV_COLLECTION']),now=NOW,production=False)

    def change_recipe(self,mutate):
        base='render-evidence/native_fixture';recipe=json.loads((self.root/(base+'/recipe.json')).read_text());mutate(recipe)
        recipe['recipe_sha256']=digest({k:v for k,v in recipe.items() if k!='recipe_sha256'});json_file(self.root,base+'/recipe.json',recipe)
        n=json.loads((self.root/self.path).read_text());n['recipe_sha256']=recipe['recipe_sha256'];json_file(self.root,self.path,n)
        old=json.loads((self.root/(base+'/ARTIFACT_MANIFEST.json')).read_text());seal=manifest(self.root,[x['path'] for x in old['artifacts']],n['recipe_sha256']);json_file(self.root,base+'/ARTIFACT_MANIFEST.json',seal)
        self.exp['recipe_sha256']=n['recipe_sha256'];self.exp['artifact_manifest_sha256']=seal['manifest_sha256']
    def test_pinned_recipe_width_must_match_decoded_receipt(self):
        self.change_recipe(lambda r:r['composition'].update(width=128))
        with self.assertRaisesRegex(BenchmarkError,'NATIVE_RECIPE_COMPOSITION'):self.inspect()
    def test_pinned_recipe_duration_must_match_frame_plan(self):
        self.change_recipe(lambda r:r['composition'].update(duration_in_frames=9))
        with self.assertRaisesRegex(BenchmarkError,'NATIVE_RECIPE_COMPOSITION'):self.inspect()
    def test_boolean_frame_zero_is_not_integer_plan(self):
        self.change_recipe(lambda r:r['plan'].update(first_frame=False))
        with self.assertRaisesRegex(BenchmarkError,'NATIVE_RECIPE_PLAN'):self.inspect()
    def test_invalid_tool_digest_in_pinned_recipe_rejected(self):
        self.change_recipe(lambda r:r.update(cli_sha256='not-a-sha'))
        with self.assertRaises(BenchmarkError):self.inspect()
