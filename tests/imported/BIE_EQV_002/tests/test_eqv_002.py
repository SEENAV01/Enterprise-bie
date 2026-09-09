import unittest
from app.bie.math_intelligence.numerical_equivalence import *
class T(unittest.TestCase):
 def test_equal(self): self.assertTrue(compare(1,.9999999999,rel_tol=1e-8).equivalent)
 def test_false(self): self.assertFalse(compare(1,2).equivalent)
 def test_error(self): self.assertEqual(compare(2,3).absolute_error,1)
 def test_tol(self):
  with self.assertRaises(ValueError):compare(1,1,-1)
if __name__=="__main__":unittest.main()
