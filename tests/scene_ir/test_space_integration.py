import unittest
from bie.scene_ir.normalized_geometry import *
from bie.scene_ir.anchor_contract import *
from bie.scene_ir.relative_constraints import *
from bie.scene_ir.alignment_constraints import *
from bie.scene_ir.grouping import *
from bie.scene_ir.z_order import *
from bie.scene_ir.camera_intent import *
class T(unittest.TestCase):
 def test_spatial_bundle(self):
  b1=make_box(.1,.1,.3,.3);b2=make_box(.6,.1,.3,.3)
  a1=anchor_for_box("a1","e1","right",b1);a2=anchor_for_box("a2","e2","left",b2)
  self.assertLess(a1.x,a2.x)
  self.assertEqual(validate_relative_constraints([RelativeConstraint("r","e1","left_of","e2",.1)]),())
  self.assertEqual(alignment_key(AlignmentConstraint("al",("e1","e2"),"y","center"))[:2],("y","center"))
  self.assertTrue(validate_groups([SceneGroup("g",("e1","e2"))]))
  self.assertEqual([x.element_id for x in resolve_z_order([ZOrderEntry("e1",1),ZOrderEntry("e2",2)])],["e1","e2"])
  self.assertTrue(require_accessible_camera(CameraIntent("cam","zoom",("e1","e2"),"fit_targets",True,"static_focus"),True))
 def test_contradiction_detected(self):
  c=validate_relative_constraints([RelativeConstraint("a","x","left_of","y"),RelativeConstraint("b","x","right_of","y")])
  self.assertEqual(len(c),2)
