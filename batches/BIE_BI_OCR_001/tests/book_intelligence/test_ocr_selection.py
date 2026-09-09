
import unittest
from book_intelligence.ocr_selection import *
class T(unittest.TestCase):
 def test_native(self):self.assertEqual(select({"native_text_ratio":.9,"native_text_quality":.95}),"NATIVE_TEXT")
 def test_full(self):self.assertEqual(select({"native_text_ratio":0,"native_text_quality":0,"has_page_image":True}),"FULL_OCR")
 def test_hybrid(self):self.assertEqual(select({"native_text_ratio":.5,"native_text_quality":.8,"has_page_image":True}),"HYBRID_RECONCILE")
 def test_text_only(self):self.assertEqual(select({"native_text_ratio":.2}),"NATIVE_TEXT")
 def test_none(self):
  with self.assertRaises(OCRSelectionError):select({})
if __name__=="__main__":unittest.main()
