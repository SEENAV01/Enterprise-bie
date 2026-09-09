import unittest
from book_intelligence.roundtrip_coverage import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertTrue(audit(["a"],["a"])["passed"])
  self.assertFalse(audit(["a","b"],["a"],["b"])["passed"])
  self.assertEqual(audit(["a"],["a","x"])["extra"],("x",))
  with self.assertRaises(E):audit(["a"],[],["x"])
if __name__=='__main__':unittest.main()
