import unittest,copy,tempfile
from pathlib import Path
from bie.evaluation.benchmarks.models import BenchmarkError
from bie.evaluation.benchmarks.av.native import *
from h2_support import report,native,CONTRACT
class H2009(unittest.TestCase):
 def setUp(self):self.r=report('mp4');self.n=native(self.r)
 def map(self):return map_render_receipt(self.n,self.r,expected_commit=COMMIT,expected_run_id='native_fixture',expected_input_sha256='a'*64,expected_recipe_sha256='b'*64,expected_composition_id='Lesson',contract_path=CONTRACT)
 def test_exact_contract_blob(self):self.assertEqual(verify_contract_bytes(CONTRACT,COMMIT)['git_blob_sha1'],CONTRACT_BLOB)
 def test_declared_native_fields_match_real_bytes(self):self.assertEqual(self.map()['status'],'DECLARATIONS_MATCH_OBSERVED_BYTES')
 def test_mapping_not_authentication(self):r=self.map();self.assertFalse(r['native_execution_verified']);self.assertFalse(r['source_provenance_verified']);self.assertFalse(r['release_authorized'])
 def test_altered_contract_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'contract.py';p.write_bytes(CONTRACT.read_bytes()+b'\n')
   with self.assertRaises(BenchmarkError):verify_contract_bytes(p,COMMIT)
 def test_other_commit_rejected(self):
  with self.assertRaises(BenchmarkError):verify_contract_bytes(CONTRACT,'0'*40)
 def test_unknown_schema(self):
  self.n['schema_version']='v1'
  with self.assertRaises(BenchmarkError):self.map()
 def test_smoke_render_rejected(self):
  self.n['mode']='smoke'
  with self.assertRaises(BenchmarkError):self.map()
 def test_injected_runner_rejected(self):
  self.n['execution_kind']='INJECTED_TEST_RUNNER'
  with self.assertRaises(BenchmarkError):self.map()
 def test_self_claimed_acceptance_rejected(self):
  self.n['accepted']=True
  with self.assertRaises(BenchmarkError):self.map()
 def test_artifact_hash_binding(self):
  self.n['artifact_sha256']='c'*64
  with self.assertRaises(BenchmarkError):self.map()
 def test_artifact_size_binding(self):
  self.n['artifact_size_bytes']+=1
  with self.assertRaises(BenchmarkError):self.map()
 def test_recipe_binding(self):
  self.n['recipe_sha256']='c'*64
  with self.assertRaises(BenchmarkError):self.map()
 def test_dimensions_binding(self):
  self.n['media']['width']=128
  with self.assertRaises(BenchmarkError):self.map()
 def test_frame_count_binding(self):
  self.n['expected_frames']=7
  with self.assertRaises(BenchmarkError):self.map()
 def test_path_traversal(self):
  self.n['output_path']='../out.mp4'
  with self.assertRaises(BenchmarkError):self.map()
 def test_forged_mp4_name_for_mkv_blocked(self):
  self.r=report();self.n=native(self.r)
  with self.assertRaises(BenchmarkError):self.map()
 def test_exact_field_roster(self):
  self.n['ignored']='untrusted'
  with self.assertRaises(BenchmarkError):self.map()
 def test_failed_local_evidence_cannot_map(self):
  self.r=report('corrupt')
  with self.assertRaises(BenchmarkError):self.map()
 def test_adapter_fields_exact_match_canonical_ast(self):
  import ast
  tree=ast.parse(CONTRACT.read_text());classes={n.name:n for n in tree.body if isinstance(n,ast.ClassDef)}
  for cls,expected in (('RenderReceipt',FIELDS),('MediaProbe',MEDIA_FIELDS)):
   actual={n.target.id for n in classes[cls].body if isinstance(n,ast.AnnAssign)};self.assertEqual(actual,expected)
