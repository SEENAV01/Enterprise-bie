import unittest
from bie.math_intelligence.derivation_step import *
class T(unittest.TestCase):
 def test_step(self): self.assertEqual(make_step("x+1=2","x=1","subtract 1","same operation both sides").rule,"subtract 1")
 def test_source(self): self.assertEqual(make_step("a","b","r","j","p4:eq2").source,"p4:eq2")
 def test_same(self):
  with self.assertRaises(ValueError):make_step("x","x","r","j")
 def test_missing(self):
  with self.assertRaises(ValueError):make_step("x","y","","j")
if __name__=="__main__":unittest.main()
