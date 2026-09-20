import unittest
from bie.visual_intelligence.constraint_solver_hardened import *
def n(i,x,y,w=.2,h=.2):return Node(i,Box(x,y,w,h))
class T(unittest.TestCase):
 def test_align(self):self.assertTrue(solve([n("a",.1,.1),n("b",.5,.5)],[Constraint("c","align_left",("a","b"))]).solved)
 def test_left(self):self.assertTrue(solve([n("a",.1,.1),n("b",.2,.1)],[Constraint("c","left_of",("a","b"),.05)]).solved)
 def test_contains(self):self.assertTrue(solve([n("p",.1,.1,.6,.6),n("c",.8,.8,.1,.1)],[Constraint("x","contains",("p","c"))]).solved)
 def test_minwidth(self):self.assertTrue(solve([n("a",.1,.1,.1,.2)],[Constraint("w","min_width",("a",),.3)]).solved)
 def test_nonoverlap(self):self.assertTrue(solve([n("a",.1,.1),n("b",.15,.15)],[Constraint("n","non_overlap",("a","b"),.01)]).solved)
 def test_unsat_contains(self):
  r=solve([n("p",.1,.1,.2,.2),n("c",.1,.1,.5,.5)],[Constraint("x","contains",("p","c"))]);self.assertFalse(r.solved);self.assertIn("x",r.unsat_core)
 def test_unsat_left(self):
  r=solve([n("a",.8,.1,.2,.2),n("b",.9,.1,.1,.2)],[Constraint("x","left_of",("a","b"),.1)]);self.assertFalse(r.solved)
 def test_repairs(self):self.assertTrue(solve([n("a",.1,.1),n("b",.2,.1)],[Constraint("c","left_of",("a","b"),.05)]).repairs)
