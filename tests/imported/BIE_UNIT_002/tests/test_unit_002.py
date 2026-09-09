import unittest
from bie.math_intelligence.si_normalization import *
class T(unittest.TestCase):
 def test_km(self): self.assertEqual(normalize_unit("km").factor,1000)
 def test_g(self): self.assertEqual(normalize_unit("g").si_symbol,"kg")
 def test_si(self): self.assertEqual(normalize_unit("N").factor,1)
 def test_bad(self):
  with self.assertRaises(ValueError):normalize_unit("furlong")
if __name__=="__main__":unittest.main()
