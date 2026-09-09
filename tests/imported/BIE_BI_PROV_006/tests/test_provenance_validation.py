import unittest
from book_intelligence.provenance_validation import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(validate([{"artifact_id":"x","anchor_ids":["a"]}],["a"])["artifacts"],1)
  with self.assertRaises(E):validate([{"artifact_id":"x","anchor_ids":["z"]}],["a"])
  with self.assertRaises(E):validate([{"artifact_id":"x","anchor_ids":[]}],["a"])
  self.assertEqual(validate([],[])["artifacts"],0)
if __name__=="__main__":unittest.main()
