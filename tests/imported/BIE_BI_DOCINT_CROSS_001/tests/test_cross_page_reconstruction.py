import unittest
from book_intelligence.cross_page_reconstruction import *
class T(unittest.TestCase):
 def test_contract(self):
  x=[{"object_id":"t","page":2,"order":1,"text":"B"},{"object_id":"t","page":1,"order":1,"text":"A"}]
  self.assertEqual(reconstruct(x)["text"],"A B")
  self.assertEqual(reconstruct(x)["pages"],(1,2))
  with self.assertRaises(E):reconstruct([])
  with self.assertRaises(E):reconstruct([{"object_id":"a","page":1,"order":1,"text":"x"},{"object_id":"b","page":2,"order":1,"text":"y"}])
if __name__=='__main__':unittest.main()
