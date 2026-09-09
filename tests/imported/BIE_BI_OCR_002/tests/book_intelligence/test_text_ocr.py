
import unittest
from bie.document_intelligence.text_ocr import *
class T(unittest.TestCase):
 def test_ok(self):self.assertEqual(normalize_tokens([{"text":"A","confidence":.9,"box":[0,0,1,1]}])[0].text,"A")
 def test_skip(self):self.assertEqual(len(normalize_tokens([{"text":" "},{"text":"B","confidence":1,"box":[0,0,1,1]}])),1)
 def test_conf(self):
  with self.assertRaises(TextOCRError):normalize_tokens([{"text":"A","confidence":2,"box":[0,0,1,1]}])
 def test_box(self):
  with self.assertRaises(TextOCRError):normalize_tokens([{"text":"A","confidence":1,"box":[0,1]}])
 def test_empty(self):
  with self.assertRaises(TextOCRError):normalize_tokens([])
if __name__=="__main__":unittest.main()
