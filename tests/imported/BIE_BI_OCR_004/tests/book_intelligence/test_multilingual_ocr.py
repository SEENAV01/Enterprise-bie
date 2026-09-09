
import unittest
from bie.document_intelligence.multilingual_ocr import *
class T(unittest.TestCase):
 def test_rank(self):self.assertEqual(choose_languages({"hi":.9,"en":.8}),("hi","en"))
 def test_limit(self):self.assertEqual(len(choose_languages({"a":1,"b":.9},1)),1)
 def test_tie(self):self.assertEqual(choose_languages({"b":1,"a":1}),("a","b"))
 def test_empty(self):
  with self.assertRaises(LanguageError):choose_languages({})
 def test_valid(self):self.assertTrue(validate_language_result("en",.8))
 def test_bad(self):
  with self.assertRaises(LanguageError):validate_language_result("",.8)
if __name__=="__main__":unittest.main()
