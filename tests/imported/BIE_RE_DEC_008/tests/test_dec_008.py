import unittest
from bie.reasoning.example_decision import *
class T(unittest.TestCase):
 def test_pick(self):
  a=Example("a",1,.5,1);b=Example("b",.2,.5,.2);self.assertEqual(decide([b,a],.5).id,"a")
 def test_diff(self):self.assertEqual(decide([Example("a",1,.2,1),Example("b",1,.8,1)],.8).id,"b")
 def test_empty(self):
  with self.assertRaises(ValueError):decide([],.5)
 def test_target(self):
  with self.assertRaises(ValueError):decide([Example("a",1,.5,1)],2)
