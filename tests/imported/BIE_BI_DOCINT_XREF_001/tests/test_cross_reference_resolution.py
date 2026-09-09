import unittest
from bie.document_intelligence.cross_reference_resolution import *
class T(unittest.TestCase):
 def test_contract(self):
  idx={("fig","3.2"):"f32"};r=resolve("See Fig. 3.2",idx);self.assertTrue(r[0]["resolved"])
  self.assertEqual(r[0]["target_id"],"f32")
  self.assertFalse(resolve("See Eq. 2",{})[0]["resolved"])
  self.assertEqual(resolve("No reference",{}),())
if __name__=='__main__':unittest.main()
