import unittest
from bie.knowledge_intelligence.example_extraction import *
class T(unittest.TestCase):
 def test_contract(self):
  b=[{"id":"e","kind":"example","text":"A ball falls","anchor_id":"p"}];self.assertEqual(len(extract(b)),1)
  self.assertEqual(extract(b)[0]["anchor_id"],"p")
  self.assertEqual(extract([{"id":"p","kind":"paragraph","text":"x"}]),())
  with self.assertRaises(E):extract([{"id":"e","kind":"example","text":"","anchor_id":"p"}])
if __name__=='__main__':unittest.main()
