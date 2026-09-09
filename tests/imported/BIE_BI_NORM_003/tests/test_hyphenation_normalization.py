import unittest
from bie.document_intelligence.hyphenation_normalization import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(repair("elec-\ntron"),"electron")
  self.assertEqual(repair("well-\nBeing"),"well-\nBeing")
  self.assertEqual(repair("x-y"),"x-y")
  with self.assertRaises(E):repair(None)
if __name__=="__main__":unittest.main()
