import unittest
from bie.document_intelligence.semantic_reading_flow import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertTrue(validate([{"id":"f","kind":"figure"},{"id":"c","kind":"caption"}])["passed"])
  self.assertFalse(validate([{"id":"c","kind":"caption"}])["passed"])
  self.assertTrue(validate([])["passed"])
  with self.assertRaises(E):validate([{"id":"x","kind":"unknown"}])
if __name__=='__main__':unittest.main()
