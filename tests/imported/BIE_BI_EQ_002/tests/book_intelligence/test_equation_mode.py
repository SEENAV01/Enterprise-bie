import unittest
from bie.document_intelligence.equation_mode import *
class T(unittest.TestCase):
    def test_inline(self): self.assertEqual(classify({"line_fraction":.2}),"INLINE")
    def test_display_size(self): self.assertEqual(classify({"line_fraction":.8}),"DISPLAY")
    def test_display_isolated(self): self.assertEqual(classify({"isolated":True}),"DISPLAY")
    def test_display_center(self): self.assertEqual(classify({"centered":True}),"DISPLAY")
    def test_bad(self):
        with self.assertRaises(EquationModeError): classify({"line_fraction":2})
if __name__=="__main__": unittest.main()
