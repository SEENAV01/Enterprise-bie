
import unittest
from bie.infrastructure.document_defense import *
class T(unittest.TestCase):
 def ok(self):return {"bytes":100,"pages":2}
 def test_ok(self):self.assertTrue(validate_document(self.ok()))
 def test_size(self):
  x=self.ok();x["bytes"]=0
  with self.assertRaises(DocumentSecurityError):validate_document(x)
 def test_pages(self):
  x=self.ok();x["pages"]=6000
  with self.assertRaises(DocumentSecurityError):validate_document(x)
 def test_embedded(self):
  x=self.ok();x["embedded_files"]=1
  with self.assertRaises(DocumentSecurityError):validate_document(x)
 def test_js(self):
  x=self.ok();x["javascript"]=True
  with self.assertRaises(DocumentSecurityError):validate_document(x)
 def test_zipbomb(self):
  x=self.ok();x["compression_ratio"]=101
  with self.assertRaises(DocumentSecurityError):validate_document(x)
if __name__=="__main__":unittest.main()
