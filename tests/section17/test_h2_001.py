import unittest,tempfile,os,hashlib,json
from pathlib import Path
from bie.evaluation.benchmarks.models import BenchmarkError
from bie.evaluation.benchmarks.av.custody import *
class H2001(unittest.TestCase):
 def setUp(self):self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.p=Path(self.t.name)/'source.bin';self.p.write_bytes(b'abc');self.sha=hashlib.sha256(b'abc').hexdigest()
 def test_frozen_bytes_and_binding(self):
  with frozen_artifact(self.p,self.sha) as (f,r):self.assertEqual(f.read_bytes(),b'abc');self.assertEqual(r,{'sha256':self.sha,'bytes':3});self.assertNotEqual(f,self.p)
  self.assertFalse(f.exists())
 def test_source_mutation_cannot_change_private_copy(self):
  with frozen_artifact(self.p,self.sha) as (f,r):self.p.write_bytes(b'xyz');self.assertEqual(f.read_bytes(),b'abc')
 def test_wrong_hash_rejected(self):
  with self.assertRaises(BenchmarkError):
   with frozen_artifact(self.p,'0'*64):pass
 def test_input_budget(self):
  with self.assertRaises(BenchmarkError):
   with frozen_artifact(self.p,self.sha,Limits(max_input_bytes=2)):pass
 def test_empty_input(self):
  self.p.write_bytes(b'')
  with self.assertRaises(BenchmarkError):
   with frozen_artifact(self.p,hashlib.sha256(b'').hexdigest()):pass
 def test_final_symlink(self):
  q=self.p.with_name('link');q.symlink_to(self.p)
  with self.assertRaises(BenchmarkError):regular_path(q)
 def test_parent_symlink(self):
  d=self.p.parent/'linkdir';d.symlink_to(self.p.parent,target_is_directory=True)
  with self.assertRaises(BenchmarkError):regular_path(d/'source.bin')
 def test_traversal(self):
  with self.assertRaises(BenchmarkError):regular_path(str(self.p.parent)+'/../source.bin')
 def test_directory_rejected(self):
  with self.assertRaises(BenchmarkError):regular_path(self.p.parent)
 def test_fifo_nonblocking_rejection(self):
  q=self.p.with_name('fifo');os.mkfifo(q)
  with self.assertRaises(BenchmarkError):regular_path(q)
 def test_resource_types_and_bounds(self):
  for k,v in [('max_frames',True),('max_input_bytes',0),('deadline_s',float('nan')),('max_width',8000),('max_audio_channels',33)]:
   with self.subTest(k=k),self.assertRaises(BenchmarkError):Limits(**{k:v})
 def test_json_duplicate_keys_rejected(self):
  self.p.write_text('{"a":1,"a":2}')
  with self.assertRaises(BenchmarkError):read_json(self.p)
 def test_json_budget(self):
  with self.assertRaises(BenchmarkError):read_json(self.p,maximum=2)
 def test_json_invalid_encoding(self):
  self.p.write_bytes(b'\xff')
  with self.assertRaises(BenchmarkError):read_json(self.p)
 def test_hash_and_size_stream(self):self.assertEqual(sha_file(self.p),(self.sha,3))
 def test_numeric_boolean_not_integer(self):
  with self.assertRaises(BenchmarkError):integer(True)
