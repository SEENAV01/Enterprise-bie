import unittest
from bie.reasoning.assessment_decision import *
class T(unittest.TestCase):
 def test_pick(self):self.assertEqual(decide([Assessment("recall",.6,.4,.2),Assessment("transfer",.9,.8,1)]).kind,"transfer")
 def test_empty(self):
  with self.assertRaises(ValueError):decide([])
 def test_range(self):
  with self.assertRaises(ValueError):decide([Assessment("x",2,1,1)])
 def test_tie(self):self.assertEqual(decide([Assessment("a",1,1,1),Assessment("b",1,1,1)]).kind,"b")
