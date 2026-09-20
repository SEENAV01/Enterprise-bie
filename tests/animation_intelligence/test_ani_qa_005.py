import unittest
from bie.animation_intelligence.animation_benchmark import *
class T(unittest.TestCase):
 def good(self,emp=True):return Case("c",.95,.92,.90,.94,.96,emp)
 def test_pass(self):self.assertEqual(run([self.good()]).status,"PASS")
 def test_floor(self):self.assertEqual(run([Case("c",.7,.9,.9,.9,.9,True)]).status,"BLOCKED")
 def test_aggregate(self):self.assertEqual(run([Case("c",.81,.81,.81,.81,.81,True)],aggregate_floor=.9).status,"BLOCKED")
 def test_missing(self):self.assertEqual(run([Case("c",None,.9,.9,.9,.9,True)]).status,"BLOCKED")
 def test_empirical_notrun(self):self.assertEqual(run([self.good(None)],require_empirical=True).status,"BLOCKED")
 def test_empirical_fail(self):self.assertEqual(run([self.good(False)]).status,"BLOCKED")
 def test_duplicate(self):
  with self.assertRaises(AnimationQAError):run([self.good(),self.good()])
 def test_accept(self):self.assertFalse(run([self.good()]).accepted)
