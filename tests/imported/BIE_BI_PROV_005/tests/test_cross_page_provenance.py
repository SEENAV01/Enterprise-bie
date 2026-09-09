import unittest
from bie.document_intelligence.cross_page_provenance import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(len(validate([{"page":1,"order":1,"anchor_id":"a"},{"page":2,"order":1,"anchor_id":"b"}])),2)
  with self.assertRaises(E):validate([])
  with self.assertRaises(E):validate([{"page":2,"order":1,"anchor_id":"a"},{"page":1,"order":1,"anchor_id":"b"}])
  with self.assertRaises(E):validate([{"page":1,"order":1,"anchor_id":""}])
if __name__=="__main__":unittest.main()
