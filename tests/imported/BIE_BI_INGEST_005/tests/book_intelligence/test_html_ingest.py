
import unittest
from bie.document_intelligence.html_ingest import *
class A:
 def inspect(self,h):return {"blocks":[{"kind":"p","text":"x"}],"links":["/a"],"title":"T"}
class T(unittest.TestCase):
 def test_ok(self):self.assertEqual(ingest_html(A(),"<p>x</p>","https://e.com")["title"],"T")
 def test_link(self):self.assertEqual(ingest_html(A(),"x","https://e.com")["links"][0],"https://e.com/a")
 def test_empty(self):
  class E:
   def inspect(self,h):return {}
  with self.assertRaises(HTMLError):ingest_html(E(),"x")
 def test_scheme(self):
  class E:
   def inspect(self,h):return {"blocks":[{"kind":"p"}],"links":["javascript:x"]}
  with self.assertRaises(HTMLError):ingest_html(E(),"x")
if __name__=="__main__":unittest.main()
