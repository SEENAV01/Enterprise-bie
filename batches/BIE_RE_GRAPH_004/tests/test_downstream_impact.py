import unittest
from app.bie.reasoning.downstream_impact import *
class T(unittest.TestCase):
 def test_direct(self):self.assertEqual(impacted(["a","b"],[("a","b")],"a"),("b",))
 def test_transitive(self):self.assertEqual(impacted(["a","b","c"],[("a","b"),("b","c")],"a"),("b","c"))
 def test_none(self):self.assertEqual(impacted(["a"],[],"a"),())
 def test_bad(self):
  with self.assertRaises(ValueError):impacted(["a"],[],"x")
