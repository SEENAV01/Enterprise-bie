import unittest,tempfile,hashlib
from pathlib import Path
from bie.compiler.compiler_asset_common import CompilerAssetRecord
from bie.compiler.asset_bundler import *
class T(unittest.TestCase):
 def make(self,td,name="a.png",data=b"abc",aid="img"):
  p=Path(td)/name;p.write_bytes(data);h=hashlib.sha256(data).hexdigest()
  return CompilerAssetRecord(aid,str(p),h,"image/png","user_supplied",True)
 def test_bundle(self):
  with tempfile.TemporaryDirectory() as td,tempfile.TemporaryDirectory() as out:
   r=bundle_assets([self.make(td)],out);self.assertTrue(r.passed);self.assertEqual(len(r.bundled),1)
 def test_public_path(self):
  with tempfile.TemporaryDirectory() as td,tempfile.TemporaryDirectory() as out:
   r=bundle_assets([self.make(td)],out);self.assertTrue(r.bundled[0].public_path.startswith("assets/"))
 def test_copy(self):
  with tempfile.TemporaryDirectory() as td,tempfile.TemporaryDirectory() as out:
   r=bundle_assets([self.make(td)],out);self.assertTrue((Path(out)/"public"/r.bundled[0].public_path).is_file())
 def test_hash_block(self):
  with tempfile.TemporaryDirectory() as td,tempfile.TemporaryDirectory() as out:
   rec=self.make(td);bad=CompilerAssetRecord(rec.asset_id,rec.source_path,"0"*64,rec.media_type,rec.rights_basis,True)
   self.assertFalse(bundle_assets([bad],out).passed)
 def test_current(self):
  with tempfile.TemporaryDirectory() as td,tempfile.TemporaryDirectory() as out:
   rec=self.make(td);bad=CompilerAssetRecord(rec.asset_id,rec.source_path,rec.expected_sha256,rec.media_type,rec.rights_basis,False)
   self.assertFalse(bundle_assets([bad],out).passed)
 def test_not_accepted(self):
  with tempfile.TemporaryDirectory() as td,tempfile.TemporaryDirectory() as out:
   self.assertFalse(bundle_assets([self.make(td)],out).accepted)
