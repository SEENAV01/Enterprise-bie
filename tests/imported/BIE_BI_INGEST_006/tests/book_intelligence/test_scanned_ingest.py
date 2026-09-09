
import unittest
from bie.document_intelligence.scanned_ingest import *
class A:
 def render_pages(self,d):return [{"image_ref":"h1","width":100,"height":200},{"image_ref":"h2","width":100,"height":200}]
class T(unittest.TestCase):
 def test_pages(self):self.assertEqual(len(ingest_scanned(A(),b"x")),2)
 def test_number(self):self.assertEqual(ingest_scanned(A(),b"x")[1].page,2)
 def test_empty(self):
  class E:
   def render_pages(self,d):return []
  with self.assertRaises(ScanError):ingest_scanned(E(),b"x")
 def test_dims(self):
  class E:
   def render_pages(self,d):return [{"image_ref":"x","width":0,"height":1}]
  with self.assertRaises(ScanError):ingest_scanned(E(),b"x")
 def test_ref(self):
  class E:
   def render_pages(self,d):return [{"width":1,"height":1}]
  with self.assertRaises(ScanError):ingest_scanned(E(),b"x")
if __name__=="__main__":unittest.main()
