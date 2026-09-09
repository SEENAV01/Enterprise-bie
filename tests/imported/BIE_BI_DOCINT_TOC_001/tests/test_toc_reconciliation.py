import unittest
from book_intelligence.toc_reconciliation import *
class T(unittest.TestCase):
 def test_contract(self):
  r=reconcile([{"title":"Force","page":2}],[{"id":"s1","title":"Force"}]);self.assertEqual(r["matches"][0]["detected_id"],"s1")
  self.assertEqual(reconcile([{"title":"X"}],[])["unmatched"],("X",))
  self.assertEqual(reconcile([],[])["matches"],())
  with self.assertRaises(E):reconcile([{"title":" "}],[])
if __name__=='__main__':unittest.main()
