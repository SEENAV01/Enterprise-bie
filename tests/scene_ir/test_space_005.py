import unittest
from bie.scene_ir.grouping import *
class T(unittest.TestCase):
 def test_pass(self):self.assertTrue(validate_groups([SceneGroup("g",("a","b"))]))
 def test_member(self):
  with self.assertRaises(SpaceIRError):SceneGroup("g",())
 def test_dup_member(self):
  with self.assertRaises(SpaceIRError):SceneGroup("g",("a","a"))
 def test_mode(self):
  with self.assertRaises(SpaceIRError):SceneGroup("g",("a",),transform_mode="free")
 def test_dup_group(self):
  with self.assertRaises(SpaceIRError):validate_groups([SceneGroup("g",("a",)),SceneGroup("g",("b",))])
