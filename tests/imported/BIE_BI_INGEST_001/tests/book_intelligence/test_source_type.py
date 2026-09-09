
import unittest
from book_intelligence.source_type import *
class T(unittest.TestCase):
 def test_pdf(self):self.assertEqual(classify("a.pdf","application/pdf").kind,"pdf")
 def test_scan(self):self.assertEqual(classify("a.pdf","application/pdf",True).kind,"scanned_pdf")
 def test_epub(self):self.assertEqual(classify("a.epub","application/epub+zip").kind,"epub")
 def test_docx(self):self.assertEqual(classify("a.docx","x").kind,"docx")
 def test_html(self):self.assertEqual(classify("a.htm","text/html").kind,"html")
 def test_bad(self):
  with self.assertRaises(SourceTypeError):classify("a.exe","x")
if __name__=="__main__":unittest.main()
