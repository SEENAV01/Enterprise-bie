import unittest
from bie.scene_ir.camera_intent import *
class T(unittest.TestCase):
 def test_static(self):self.assertTrue(require_accessible_camera(CameraIntent("c","static",("a",),"wide"),True))
 def test_pan(self):self.assertEqual(CameraIntent("c","pan",("a",),"medium").mode,"pan")
 def test_target(self):
  with self.assertRaises(SpaceIRError):CameraIntent("c","static",(),"wide")
 def test_motion_guard(self):
  with self.assertRaises(SpaceIRError):CameraIntent("c","pan",("a",),"wide",False)
 def test_reduced(self):
  with self.assertRaises(SpaceIRError):require_accessible_camera(CameraIntent("c","orbit",("a",),"wide"),True)
 def test_reduced_fallback(self):self.assertTrue(require_accessible_camera(CameraIntent("c","orbit",("a",),"wide",True,"static_focus"),True))
