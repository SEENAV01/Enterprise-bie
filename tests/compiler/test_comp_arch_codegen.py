import unittest,tempfile,json
from pathlib import Path
from bie.compiler.deterministic_codegen import *
class T(unittest.TestCase):
 def plan(self,files=None):
  return plan_deterministic_codegen(scene_fingerprint="a"*64,compiler_version="1.0.0",deterministic_seed=7,component_snapshot=(("text","TextElement"),),files=files or [("src/B.tsx","B\r\n"),("src/A.tsx","A")])
 def test_deterministic(self):self.assertEqual(self.plan().manifest_sha256,self.plan([("src/A.tsx","A\n"),("src/B.tsx","B")]).manifest_sha256)
 def test_order(self):self.assertEqual([f.path for f in self.plan().files],["src/A.tsx","src/B.tsx"])
 def test_newlines(self):self.assertEqual(self.plan().files[0].content,"A\n")
 def test_duplicate(self):
  with self.assertRaises(DeterministicCodegenError):self.plan([("a","x"),("a","y")])
 def test_traversal(self):
  with self.assertRaises(DeterministicCodegenError):self.plan([("../x","x")])
 def test_write(self):
  with tempfile.TemporaryDirectory() as td:
   files=write_codegen_plan(self.plan(),td);self.assertEqual(files,("src/A.tsx","src/B.tsx"));self.assertTrue((Path(td)/"CODEGEN_MANIFEST.json").is_file())
 def test_not_accepted(self):self.assertFalse(self.plan().accepted)
