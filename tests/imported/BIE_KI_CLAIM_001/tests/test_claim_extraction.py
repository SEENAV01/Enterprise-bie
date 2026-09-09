import unittest
from knowledge_intelligence.claim_extraction import *
class T(unittest.TestCase):
 def test_contract(self):
  b=[{"id":"b","anchor_id":"p","claims":["Force changes motion"]}];self.assertEqual(len(extract(b)),1)
  self.assertEqual(extract(b)[0]["claim_id"],"b:c0")
  self.assertEqual(extract([]),())
  with self.assertRaises(E):extract([{"id":"b","anchor_id":"","claims":["x"]}])
if __name__=='__main__':unittest.main()
