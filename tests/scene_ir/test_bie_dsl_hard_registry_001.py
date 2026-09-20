import unittest
from bie.scene_ir.unified_scene_ir_contract import *
from bie.scene_ir.scene_ir_registry import *
class T(unittest.TestCase):
 def make(self,etype="text",props=None,action="reveal"):
  e=UnifiedElement("e",etype,props or {"text":"Hello"},("s",),("r",))
  t=UnifiedTrack("t","e",action,0,100,{},("s",),("r",))
  return UnifiedSceneIRDocument("scene","1.0.0","Title",100,(e,),(t,),("s",),("r",))
 def test_default_counts(self):
  s=default_registry().snapshot();self.assertEqual(len(s["element_types"]),18);self.assertGreaterEqual(len(s["actions"]),10)
 def test_pass(self):self.assertEqual(default_registry().normalize_document(self.make()).scene_id,"scene")
 def test_unknown_element(self):
  with self.assertRaises(SceneIRRegistryError):default_registry().normalize_document(self.make("magic",{"x":1}))
 def test_missing_prop(self):
  with self.assertRaises(SceneIRRegistryError):default_registry().normalize_document(self.make("equation",{"x":1}))
 def test_unknown_action(self):
  with self.assertRaises(SceneIRRegistryError):default_registry().normalize_document(self.make(action="explode"))
 def test_asset_guard(self):
  with self.assertRaises(SceneIRRegistryError):default_registry().normalize_document(self.make("image",{"foo":"x"}))
