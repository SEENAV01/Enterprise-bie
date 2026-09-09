import unittest
from book_intelligence.learning_objectives import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(len(normalize([{"id":"o","text":"Explain","source_anchor":"p"}])),1)
  with self.assertRaises(E):normalize([{"id":"o","text":"","source_anchor":"p"}])
  with self.assertRaises(E):normalize([{"id":"o","text":"x","source_anchor":""}])
  self.assertEqual(normalize([]),())
if __name__=="__main__":unittest.main()
