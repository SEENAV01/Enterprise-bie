import unittest
from bie.math_intelligence.unit_parser import *
class T(unittest.TestCase):
 def test_ms(self): self.assertEqual([(x.symbol,x.exponent) for x in parse_unit("m/s").terms],[("m",1),("s",-1)])
 def test_power(self): self.assertEqual(parse_unit("m^2").terms[0].exponent,2)
 def test_product(self): self.assertEqual(len(parse_unit("kg*m/s^2").terms),3)
 def test_bad(self):
  with self.assertRaises(ValueError):parse_unit("m@x")
if __name__=="__main__":unittest.main()
