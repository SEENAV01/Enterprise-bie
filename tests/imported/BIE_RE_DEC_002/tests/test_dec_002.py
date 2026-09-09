import unittest
from bie.reasoning.prerequisite_order import decide
class T(unittest.TestCase):
 def test_order(self):self.assertEqual(decide(["b","a"],[("a","b")])[0],("a","b"))
 def test_cycle(self):self.assertFalse(decide(["a","b"],[("a","b"),("b","a")])[1])
 def test_single(self):self.assertTrue(decide(["a"],[])[1])
 def test_unknown(self):
  with self.assertRaises(ValueError):decide(["a"],[("x","a")])
