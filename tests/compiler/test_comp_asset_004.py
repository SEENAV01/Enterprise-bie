import unittest
from bie.scene_ir.unified_scene_ir_contract import UnifiedElement,UnifiedSceneIRDocument
from bie.compiler.asset_path_resolver import CompilerAssetPathRegistry
from bie.compiler.asset_bundler import BundledAsset
from bie.compiler.missing_asset_failure import *
class T(unittest.TestCase):
 def doc(self,ref="asset://img"):
  e=UnifiedElement("e","image",{"asset_ref":ref},("s",),("r",),{"alt":"x"})
  return UnifiedSceneIRDocument("scene","1.0.0","T",10,(e,),(),("s",),("r",))
 def reg(self):
  r=CompilerAssetPathRegistry();r.register(BundledAsset("img","assets/a.png","a"*64,"image/png","rights","/src/a",False));return r
 def test_pass(self):self.assertTrue(detect_missing_assets(self.doc(),self.reg()).passed)
 def test_missing(self):self.assertEqual(detect_missing_assets(self.doc("asset://x"),self.reg()).missing_count,1)
 def test_code(self):self.assertEqual(detect_missing_assets(self.doc("asset://x"),self.reg()).diagnostics[0].code,"COMP_ASSET_MISSING")
 def test_require(self):
  with self.assertRaises(CompilerAssetError):require_no_missing_assets(detect_missing_assets(self.doc("asset://x"),self.reg()))
 def test_non_asset_element(self):
  e=UnifiedElement("t","text",{"text":"x"},("s",),("r",));d=UnifiedSceneIRDocument("s","1.0.0","T",10,(e,),(),("s",),("r",));self.assertTrue(detect_missing_assets(d,self.reg()).passed)
 def test_not_accepted(self):self.assertFalse(detect_missing_assets(self.doc(),self.reg()).accepted)
