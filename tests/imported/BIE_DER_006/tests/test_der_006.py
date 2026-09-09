import unittest
from app.bie.math_intelligence.boundary_conditions import *
class T(unittest.TestCase):
 def test_make(self): self.assertEqual(make_boundary("y","x=0","1").value,"1")
 def test_complete(self): self.assertTrue(complete({("y","x=0")},[make_boundary("y","x=0","1")]))
 def test_missing(self): self.assertFalse(complete({("y","x=1")},[make_boundary("y","x=0","1")]))
 def test_bad(self):
  with self.assertRaises(ValueError):make_boundary("y","","1")
if __name__=="__main__":unittest.main()
