import unittest
from bie.document_intelligence.provenance_confidence import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertAlmostEqual(aggregate([1,.8]),.9)
  self.assertEqual(decision(.95),"ACCEPT")
  self.assertEqual(decision(.8),"REVIEW")
  self.assertEqual(decision(.5),"REJECT")
  with self.assertRaises(E):aggregate([])
if __name__=="__main__":unittest.main()
