import unittest
from bie.reasoning.graph_cycles import *
class T(unittest.TestCase):
 def test_none(self):self.assertEqual(find_cycles(["a","b"],[("a","b")]),())
 def test_cycle(self):self.assertTrue(find_cycles(["a","b"],[("a","b"),("b","a")]))
 def test_self(self):self.assertTrue(find_cycles(["a"],[("a","a")]))
 def test_bad(self):
  with self.assertRaises(ValueError):find_cycles(["a"],[("a","x")])
