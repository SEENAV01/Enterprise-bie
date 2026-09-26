import unittest,subprocess
from pathlib import Path
from bie.game_engine.operations_engine.canonical_bindings import *
ROOT=Path(__file__).resolve().parents[2]
class CanonicalBindingTests(unittest.TestCase):
 def test_all_exact(self):self.assertEqual(verify_canonical_bindings(ROOT),CANONICAL_BLOBS)
 def test_main_pinned(self):self.assertEqual(CANONICAL_MAIN,'375d99af0edd0086206817dae932156ddf61c569')
 def test_git_blob_hash_matches_files(self):
  for rel,sha in CANONICAL_BLOBS.items():self.assertEqual(git_blob_sha((ROOT/rel).read_bytes()),sha)
 def test_tamper_detected(self):
  import tempfile,shutil
  with tempfile.TemporaryDirectory() as td:
   d=Path(td)
   for rel in CANONICAL_BLOBS:
    p=d/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/rel,p)
   (d/'bie/infrastructure/idempotency_store.py').write_text('tamper')
   self.assertRaises(Exception,verify_canonical_bindings,d)
