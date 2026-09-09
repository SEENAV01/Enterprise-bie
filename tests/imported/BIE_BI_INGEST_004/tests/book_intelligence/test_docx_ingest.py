
import unittest
from book_intelligence.docx_ingest import *
class A:
 def inspect(self,d):return {"blocks":[{"kind":"heading","text":"H"},{"kind":"paragraph","text":"P"}]}
class T(unittest.TestCase):
 def test_ok(self):self.assertEqual(len(ingest_docx(A(),b"x")["blocks"]),2)
 def test_kind(self):self.assertEqual(ingest_docx(A(),b"x")["blocks"][0]["kind"],"heading")
 def test_empty(self):
  class E:
   def inspect(self,d):return {}
  with self.assertRaises(DOCXError):ingest_docx(E(),b"x")
 def test_unknown(self):
  class E:
   def inspect(self,d):return {"blocks":[{"kind":"macro"}]}
  with self.assertRaises(DOCXError):ingest_docx(E(),b"x")
if __name__=="__main__":unittest.main()
