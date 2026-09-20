import unittest
from bie.scene_ir.relative_constraints import *
class T(unittest.TestCase):
 def test_pass(self):self.assertEqual(validate_relative_constraints([RelativeConstraint("c","a","left_of","b",.1)]),())
 def test_contradiction(self):self.assertEqual(len(validate_relative_constraints([RelativeConstraint("c1","a","left_of","b"),RelativeConstraint("c2","a","right_of","b")])),2)
 def test_relation(self):
  with self.assertRaises(SpaceIRError):RelativeConstraint("c","a","nearish","b")
 def test_gap(self):
  with self.assertRaises(SpaceIRError):RelativeConstraint("c","a","left_of","b",-1)
 def test_dup(self):
  with self.assertRaises(SpaceIRError):validate_relative_constraints([RelativeConstraint("c","a","left_of","b"),RelativeConstraint("c","a","above","b")])
