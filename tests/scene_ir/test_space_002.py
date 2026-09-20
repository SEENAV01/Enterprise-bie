import unittest
from bie.scene_ir.anchor_contract import *
class T(unittest.TestCase):
 def test_center(self):self.assertEqual(anchor_for_box("a","e","center",NormalizedBox(0,0,1,1)).x,.5)
 def test_right(self):self.assertEqual(anchor_for_box("a","e","right",NormalizedBox(0,0,.5,.5)).x,.5)
 def test_custom(self):
  with self.assertRaises(SpaceIRError):anchor_for_box("a","e","custom",NormalizedBox(0,0,1,1))
 def test_kind(self):
  with self.assertRaises(SpaceIRError):Anchor("a","e","weird",.5,.5)
 def test_bounds(self):
  with self.assertRaises(SpaceIRError):Anchor("a","e","center",2,.5)
