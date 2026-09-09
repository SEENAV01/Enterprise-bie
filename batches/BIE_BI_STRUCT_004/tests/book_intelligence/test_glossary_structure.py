import unittest
from book_intelligence.glossary_structure import *
class T(unittest.TestCase):
    def test_ok(self): self.assertIn("force",normalize([{"term":"Force","definition":"interaction"}])[0])
    def test_alias(self): self.assertEqual(normalize([{"term":"Velocity","definition":"rate","aliases":["v"]}])[1]["v"],"velocity")
    def test_empty(self):
        with self.assertRaises(GlossaryError): normalize([{"term":"","definition":"x"}])
    def test_conflict(self):
        with self.assertRaises(GlossaryError): normalize([{"term":"A","definition":"x"},{"term":"a","definition":"y"}])
if __name__=="__main__": unittest.main()
