import unittest
from app.bie.math_intelligence.unit_conversion import *
class T(unittest.TestCase):
 def test_km(self): self.assertEqual(convert(2,"km","m").result,2000)
 def test_time(self): self.assertEqual(convert(2,"h","min").result,120)
 def test_mass(self): self.assertAlmostEqual(convert(500,"g","kg").result,.5)
 def test_bad(self):
  with self.assertRaises(ValueError):convert(1,"m","s")
if __name__=="__main__":unittest.main()
