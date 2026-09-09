import unittest
from bie.reasoning.game_decision import *
class T(unittest.TestCase):
 def test_pick(self):self.assertEqual(decide([Game("quiz",.5,.5,.2),Game("manipulate",1,.8,.8)]).mechanic,"manipulate")
 def test_empty(self):
  with self.assertRaises(ValueError):decide([])
 def test_range(self):
  with self.assertRaises(ValueError):decide([Game("x",2,1,1)])
 def test_tie(self):self.assertEqual(decide([Game("a",1,1,1),Game("b",1,1,1)]).mechanic,"b")
