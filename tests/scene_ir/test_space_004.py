import unittest
from bie.scene_ir.alignment_constraints import *
class T(unittest.TestCase):
 def test_pass(self):self.assertEqual(alignment_key(AlignmentConstraint("c",("a","b"),"x","center"))[0],"x")
 def test_ids(self):
  with self.assertRaises(SpaceIRError):AlignmentConstraint("c",("a",),"x","center")
 def test_axis(self):
  with self.assertRaises(SpaceIRError):AlignmentConstraint("c",("a","b"),"z","center")
 def test_mode(self):
  with self.assertRaises(SpaceIRError):AlignmentConstraint("c",("a","b"),"x","middle")
 def test_tol(self):
  with self.assertRaises(SpaceIRError):AlignmentConstraint("c",("a","b"),"x","center",-1)
