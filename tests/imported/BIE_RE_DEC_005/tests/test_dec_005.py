import unittest
from bie.reasoning.derivation_decision import decide
class T(unittest.TestCase):
 def test_pass(self):self.assertTrue(decide(1,1,1,"p")[0])
 def test_equiv(self):self.assertIn("non_equivalent",decide(0,1,1,"p")[1])
 def test_assume(self):self.assertIn("unresolved_assumptions",decide(1,1,0,"p")[1])
 def test_source(self):
  with self.assertRaises(ValueError):decide(1,1,1,"")
