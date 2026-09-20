import unittest
from bie.scene_ir.unified_scene_ir_contract import *
from bie.scene_ir.accessibility_merge import *
class T(unittest.TestCase):
 def doc(self):
  img=UnifiedElement("img","image",{"asset_ref":"asset://i"},("s",),("r",),{"alt":"Cell"});sim=UnifiedElement("sim","simulation",{"execution_class":"conceptual"},("s",),("r",),{})
  return UnifiedSceneIRDocument("s","1.0.0","T",100,(img,sim),(),("s",),("r",),accessibility_metadata=({"element_id":"sim","reduced_motion_variant":"static_state","keyboard_focusable":True},))
 def test_pass(self):self.assertTrue(merge_accessibility(self.doc())[1].passed)
 def test_merge(self):
  d,_=merge_accessibility(self.doc());m={e.element_id:e for e in d.elements};self.assertEqual(m["sim"].accessibility["reduced_motion_variant"],"static_state")
 def test_focus(self):self.assertEqual(merge_accessibility(self.doc())[1].keyboard_focus_order,("sim",))
 def test_visual_block(self):
  e=UnifiedElement("img","image",{"asset_ref":"a"},("s",),("r",),{});d=UnifiedSceneIRDocument("s","1.0.0","T",10,(e,),(),("s",),("r",));self.assertFalse(merge_accessibility(d)[1].passed)
 def test_not_accepted(self):self.assertFalse(merge_accessibility(self.doc())[1].accepted)
