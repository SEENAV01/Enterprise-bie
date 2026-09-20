import unittest
from bie.compiler.asset_path_resolver import *
from bie.compiler.asset_bundler import BundledAsset
class T(unittest.TestCase):
 def reg(self):
  r=CompilerAssetPathRegistry();r.register(BundledAsset("img","assets/a.png","a"*64,"image/png","rights","/src/a",False));return r
 def test_asset_uri(self):self.assertEqual(self.reg().require("asset://img").resolved_public_path,"assets/a.png")
 def test_plain_id(self):self.assertEqual(self.reg().require("img").resolved_public_path,"assets/a.png")
 def test_missing(self):self.assertFalse(self.reg().resolve("asset://x").passed)
 def test_require(self):
  with self.assertRaises(CompilerAssetError):self.reg().require("asset://x")
 def test_duplicate(self):
  r=self.reg()
  with self.assertRaises(CompilerAssetError):r.register(BundledAsset("img","assets/b.png","b"*64,"image/png","rights","/src/b",False))
 def test_snapshot(self):self.assertEqual(self.reg().snapshot()[0][0],"img")
