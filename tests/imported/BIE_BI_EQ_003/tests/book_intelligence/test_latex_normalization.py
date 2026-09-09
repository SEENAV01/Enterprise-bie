import unittest
from bie.document_intelligence.latex_normalization import *
class T(unittest.TestCase):
    def test_trim(self): self.assertEqual(normalize("  x + y  "),"x + y")
    def test_minus(self): self.assertEqual(normalize("x−y"),"x-y")
    def test_times(self): self.assertIn(r"\times",normalize("a×b"))
    def test_empty(self):
        with self.assertRaises(LatexNormalizeError): normalize("")
    def test_unbalanced(self):
        with self.assertRaises(LatexNormalizeError): normalize(r"\frac{a}{b")
if __name__=="__main__": unittest.main()
