import unittest
from bie.reasoning.causal_decision import *
class T(unittest.TestCase):
 def test_yes(self):self.assertTrue(decide(Evidence("A","B","m",.9,"p"))["accepted"])
 def test_no(self):self.assertFalse(decide(Evidence("A","B","m",.4,"p"))["accepted"])
 def test_reason(self):self.assertEqual(decide(Evidence("A","B","mechanism",.9,"p"))["rationale"],"mechanism")
 def test_missing(self):
  with self.assertRaises(ValueError):decide(Evidence("A","B","",.9,"p"))
