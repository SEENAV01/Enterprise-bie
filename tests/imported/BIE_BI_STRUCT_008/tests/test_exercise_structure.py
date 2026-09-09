import unittest
from bie.document_intelligence.exercise_structure import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(normalize([{"id":"q","prompt":"Why?","kind":"short_answer"}])[0]["kind"],"short_answer")
  with self.assertRaises(E):normalize([{"id":"q","prompt":"x","kind":"bad"}])
  with self.assertRaises(E):normalize([{"id":"q","prompt":""}])
  self.assertEqual(normalize([]),())
if __name__=="__main__":unittest.main()
