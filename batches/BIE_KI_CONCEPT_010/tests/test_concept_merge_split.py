import unittest
from knowledge_intelligence.concept_merge_split import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(decide("a","b",1,1,1)["action"],"MERGE")
  self.assertEqual(decide("a","b",.7,.7,.7)["action"],"REVIEW")
  self.assertEqual(decide("a","b",.2,.2,.2)["action"],"KEEP_SEPARATE")
  self.assertEqual(len(split("c",["x","y"]))["subconcepts"],2)
  with self.assertRaises(E):split("c",["x"])
if __name__=='__main__':unittest.main()
