import unittest
from app.bie.math_intelligence.operators import *
class T(unittest.TestCase):
 def test_power(self): self.assertEqual(operator_info("^").associativity,"right")
 def test_mul(self): self.assertGreater(operator_info("*").precedence,operator_info("+").precedence)
 def test_eq(self): self.assertEqual(operator_info("=").precedence,5)
 def test_unknown(self):
  with self.assertRaises(ValueError):operator_info("?")
if __name__=="__main__":unittest.main()
