import unittest
from bie.scene_ir.normalized_geometry import *
class T(unittest.TestCase):
 def test_box(self):self.assertEqual(make_box(.1,.2,.3,.4).width,.3)
 def test_point(self):self.assertEqual(normalized_point(.2,.8),(.2,.8))
 def test_denorm(self):self.assertEqual(denormalize_point((.5,.5),100,200),(50,100))
 def test_out(self):
  with self.assertRaises(SpaceIRError):make_box(.8,.8,.3,.3)
 def test_zero(self):
  with self.assertRaises(SpaceIRError):make_box(0,0,0,1)
 def test_canvas(self):
  with self.assertRaises(SpaceIRError):denormalize_point((.5,.5),0,100)
