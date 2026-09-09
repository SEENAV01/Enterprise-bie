import unittest
from bie.document_intelligence.references_structure import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(len(normalize([{"id":"r","text":"Book"}])),1)
  with self.assertRaises(E):normalize([{"id":"r","text":""}])
  with self.assertRaises(E):normalize([{"id":"r","text":"a"},{"id":"r","text":"b"}])
  self.assertEqual(normalize([]),())
if __name__=="__main__":unittest.main()
