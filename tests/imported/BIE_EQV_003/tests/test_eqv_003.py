import unittest
from bie.math_intelligence.rearrangement import *
class T(unittest.TestCase):
 def test_add(self): self.assertTrue(validate_linear_step((2,5),(5,8),"add",3).valid)
 def test_bad(self): self.assertFalse(validate_linear_step((2,5),(5,7),"add",3).valid)
 def test_zero(self): self.assertEqual(validate_linear_step((1,2),(1,2),"divide",0).reason,"division_by_zero")
 def test_unknown(self):
  with self.assertRaises(ValueError):validate_linear_step((1,1),(1,1),"sqrt",2)
if __name__=="__main__":unittest.main()
