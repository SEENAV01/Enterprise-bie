import unittest
from bie.math_intelligence.symbol_metadata import *
class T(unittest.TestCase):
 def test_var(self): self.assertEqual(make_metadata("v",unit="m/s").unit,"m/s")
 def test_constant(self): self.assertEqual(make_metadata("G","constant").role,"constant")
 def test_source(self): self.assertEqual(make_metadata("x",source="p12:eq3").source,"p12:eq3")
 def test_bad(self):
  with self.assertRaises(ValueError):make_metadata("x y")
if __name__=="__main__":unittest.main()
