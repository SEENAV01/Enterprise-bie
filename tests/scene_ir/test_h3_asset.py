import unittest
from bie.scene_ir.unified_scene_ir_contract import *
from bie.scene_ir.asset_contract import *
OWN={"title":"cell drawing","source":"bie","licence":"BIE's own drawing"}   # Task 046a-L: every asset carries its licence record
class T(unittest.TestCase):
 def doc(self,ref="asset:img"):
  e=UnifiedElement("img","image",{"asset_ref":ref},("src",),("r",),{"alt":"cell"})
  return UnifiedSceneIRDocument("s","1.0.0","T",10,(e,),(),("src",),("r",))
 def reg(self,current=True):
  r=AssetRegistry();r.register(AssetRecord("asset:img","asset://img","a"*64,"licensed","image/png",current,"src",OWN));return r
 def test_pass(self):self.assertTrue(resolve_assets(self.doc(),self.reg()).passed)
 def test_missing(self):self.assertFalse(resolve_assets(self.doc("asset:x"),self.reg()).passed)
 def test_stale(self):self.assertIn("asset_stale:asset:img",resolve_assets(self.doc(),self.reg(False)).blockers)
 def test_hash_guard(self):
  with self.assertRaises(ValueError):AssetRecord("a","u","bad","rights","image/png")
 def test_duplicate(self):
  r=self.reg()
  with self.assertRaises(ValueError):r.register(AssetRecord("asset:img","u","b"*64,"rights","image/png"))
 def test_not_accepted(self):self.assertFalse(resolve_assets(self.doc(),self.reg()).accepted)
 def test_licence_gate(self):
  # Task 046a-L: a rights word the licence policy cannot read, or a refused licence, stops the scene; CC BY passes with its credit
  def reg(rights,licence=()):
   r=AssetRegistry();r.register(AssetRecord("asset:img","asset://img","a"*64,rights,"image/png",True,"src",licence));return r
  self.assertIn("asset_licence:asset:img: refused: licence missing or unreadable",resolve_assets(self.doc(),reg("licensed")).blockers)
  self.assertTrue(any("share-alike" in b for b in resolve_assets(self.doc(),reg("CC BY-SA 4.0")).blockers))
  cc_by={"title":"Neuron","source":"wikimedia_commons","licence":"CC BY 4.0","licence_url":"https://creativecommons.org/licenses/by/4.0/",
         "author":"A. Author","page_url":"https://commons.wikimedia.org/wiki/File:Neuron.png"}
  ok=resolve_assets(self.doc(),reg("rights:neuron",cc_by))
  self.assertTrue(ok.passed)
  self.assertEqual(ok.credits,("Neuron · A. Author · CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/) · https://commons.wikimedia.org/wiki/File:Neuron.png",))
  self.assertTrue(any("missing: author" in b for b in resolve_assets(self.doc(),reg("rights:neuron",dict(cc_by,author=""))).blockers))
