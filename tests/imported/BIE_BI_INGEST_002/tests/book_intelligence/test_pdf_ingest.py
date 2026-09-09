
import unittest
from book_intelligence.pdf_ingest import *
class A:
 def inspect(self,d):return {"page_count":3,"metadata":{"title":"x"},"encrypted":False,"text_pages":2}
class T(unittest.TestCase):
 def test_ok(self):self.assertEqual(ingest_pdf(A(),b"%PDF-x").page_count,3)
 def test_meta(self):self.assertEqual(ingest_pdf(A(),b"%PDF-x").metadata["title"],"x")
 def test_bad(self):
  with self.assertRaises(PDFIngestError):ingest_pdf(A(),b"x")
 def test_empty(self):
  class E:
   def inspect(self,d):return {"page_count":0}
  with self.assertRaises(PDFIngestError):ingest_pdf(E(),b"%PDF")
if __name__=="__main__":unittest.main()
