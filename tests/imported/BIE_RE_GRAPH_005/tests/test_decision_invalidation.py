import unittest
from bie.reasoning.decision_invalidation import *
class T(unittest.TestCase):
 def test_hit(self):self.assertFalse(invalidate([("d",["e"])],["e"])[0][1])
 def test_miss(self):self.assertTrue(invalidate([("d",["e"])],["x"])[0][1])
 def test_many(self):self.assertEqual(len(invalidate([("a",[]),("b",[])],["x"])),2)
 def test_empty(self):self.assertEqual(invalidate([],["e"]),())
