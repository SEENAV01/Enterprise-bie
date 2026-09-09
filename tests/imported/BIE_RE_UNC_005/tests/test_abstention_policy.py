import unittest
from bie.reasoning.abstention_policy import *
class T(unittest.TestCase):
 def test_noevidence(self):self.assertTrue(should_abstain(.9,0)[0])
 def test_low(self):self.assertIn("low_confidence",should_abstain(.2,2)[1])
 def test_conflict(self):self.assertTrue(should_abstain(.9,2,True)[0])
 def test_pass(self):self.assertFalse(should_abstain(.9,2)[0])
