import unittest
from bie.scene_ir.unified_scene_ir_contract import *
from bie.scene_ir.asset_contract import *
class T(unittest.TestCase):
 def doc(self,ref="asset:img"):
  e=UnifiedElement("img","image",{"asset_ref":ref},("src",),("r",),{"alt":"cell"})
  return UnifiedSceneIRDocument("s","1.0.0","T",10,(e,),(),("src",),("r",))
 def reg(self,current=True):
  r=AssetRegistry();r.register(AssetRecord("asset:img","asset://img","a"*64,"licensed","image/png",current,"src"));return r
 def test_pass(self):self.assertTrue(resolve_assets(self.doc(),self.reg()).passed)
 def test_missing(self):self.assertFalse(resolve_assets(self.doc("asset:x"),self.reg()).passed)
 def test_stale(self):self.assertIn("asset_stale:asset:img",resolve_assets(self.doc(),self.reg(False)).blockers)
 def test_hash_guard(self):
  with self.assertRaises(ValueError):AssetRecord("a","u","bad","rights","image/png")
 def test_duplicate(self):
  r=self.reg()
  with self.assertRaises(ValueError):r.register(AssetRecord("asset:img","u","b"*64,"rights","image/png"))
 def test_not_accepted(self):self.assertFalse(resolve_assets(self.doc(),self.reg()).accepted)
