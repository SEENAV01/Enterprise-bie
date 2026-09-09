
import unittest
from bie.document_intelligence.epub_ingest import *
class A:
 def inspect(self,d):return {"spine":["c1","c2"],"metadata":{"title":"x"},"resources":["i.png"]}
class T(unittest.TestCase):
 def test_spine(self):self.assertEqual(len(ingest_epub(A(),b"x")["spine"]),2)
 def test_meta(self):self.assertEqual(ingest_epub(A(),b"x")["metadata"]["title"],"x")
 def test_resource(self):self.assertEqual(ingest_epub(A(),b"x")["resources"][0],"i.png")
 def test_empty(self):
  class E:
   def inspect(self,d):return {}
  with self.assertRaises(EPUBError):ingest_epub(E(),b"x")
 def test_dup(self):
  class D:
   def inspect(self,d):return {"spine":["a","a"]}
  with self.assertRaises(EPUBError):ingest_epub(D(),b"x")
if __name__=="__main__":unittest.main()
