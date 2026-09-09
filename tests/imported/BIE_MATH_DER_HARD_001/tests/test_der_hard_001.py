import unittest
from app.bie.math_intelligence.derivation_reconstruction import *
class T(unittest.TestCase):
 def test_complete(self):
  r=reconstruct("a","c",[("b","r1"),("c","r2")],lambda a,b,r:(a,b) in {("a","b"),("b","c")});self.assertTrue(r.complete)
 def test_inserted(self): self.assertEqual(reconstruct("a","c",[("b","r"),("c","r")],lambda a,b,r:True).inserted,("b",))
 def test_incomplete(self): self.assertFalse(reconstruct("a","z",[("b","r")],lambda a,b,r:b=="b").complete)
 def test_bad(self):
  with self.assertRaises(ValueError):reconstruct("","x",[],lambda *x:True)
if __name__=="__main__":unittest.main()
