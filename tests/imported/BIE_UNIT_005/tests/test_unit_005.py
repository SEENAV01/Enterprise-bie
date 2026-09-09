import unittest
from app.bie.math_intelligence.unit_mismatch import *
class T(unittest.TestCase):
 def test_ok(self): self.assertTrue(check_dimensions((1,0,-1,0,0,0,0),(1,0,-1,0,0,0,0)).compatible)
 def test_bad(self): self.assertEqual(check_dimensions((1,0,0,0,0,0,0),(0,0,1,0,0,0,0)).reason,"dimension_mismatch")
 def test_vector(self): self.assertEqual(len(check_dimensions((0,)*7,(0,)*7).left),7)
 def test_length(self):
  with self.assertRaises(ValueError):check_dimensions((1,),(1,))
if __name__=="__main__":unittest.main()
