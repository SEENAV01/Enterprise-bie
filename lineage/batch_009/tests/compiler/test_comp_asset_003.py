import unittest,tempfile,hashlib
from pathlib import Path
from bie.compiler.asset_hash_verifier import *
from bie.compiler.asset_bundler import *
from bie.compiler.compiler_asset_common import CompilerAssetRecord
class T(unittest.TestCase):
 def test_pass(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"x";p.write_bytes(b"abc");h=hashlib.sha256(b"abc").hexdigest();self.assertTrue(verify_asset_hash("x",p,h).passed)
 def test_fail(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"x";p.write_bytes(b"abc");self.assertFalse(verify_asset_hash("x",p,"0"*64).passed)
 def test_missing(self):
  with tempfile.TemporaryDirectory() as td:
   self.assertFalse(verify_asset_hash("x",Path(td)/"none","0"*64).passed)
 def test_bundle(self):
  with tempfile.TemporaryDirectory() as src,tempfile.TemporaryDirectory() as out:
   p=Path(src)/"a.png";p.write_bytes(b"abc");h=hashlib.sha256(b"abc").hexdigest()
   rec=CompilerAssetRecord("img",str(p),h,"image/png","rights",True);br=bundle_assets([rec],out)
   results=verify_bundle_hashes(br);self.assertTrue(require_all_hashes(results))
 def test_not_accepted(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"x";p.write_bytes(b"abc");h=hashlib.sha256(b"abc").hexdigest();self.assertFalse(verify_asset_hash("x",p,h).accepted)
 def test_bad_expected(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"x";p.write_bytes(b"abc")
   with self.assertRaises(Exception):verify_asset_hash("x",p,"bad")
