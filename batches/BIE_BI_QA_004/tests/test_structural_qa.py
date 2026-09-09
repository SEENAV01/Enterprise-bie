import unittest
from book_intelligence.structural_qa import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertTrue(evaluate([{"id":"c","kind":"chapter"}])["passed"])
  self.assertFalse(evaluate([{"id":"x","kind":"bad"}])["passed"])
  self.assertFalse(evaluate([{"id":"x","kind":"chapter"},{"id":"x","kind":"section"}])["passed"])
  self.assertEqual(evaluate([])["count"],0)
if __name__=="__main__":unittest.main()
