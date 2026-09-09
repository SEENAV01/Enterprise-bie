
import unittest
from book_intelligence.math_ocr import *
class T(unittest.TestCase):
 def test_ok(self):self.assertEqual(normalize({"latex":"x^2","confidence":.9,"box":[0,0,1,1]}).latex,"x^2")
 def test_display(self):self.assertTrue(normalize({"latex":"x","confidence":1,"box":[0,0,1,1],"display":True}).display)
 def test_empty(self):
  with self.assertRaises(MathOCRError):normalize({"confidence":1,"box":[0,0,1,1]})
 def test_conf(self):
  with self.assertRaises(MathOCRError):normalize({"latex":"x","confidence":-1,"box":[0,0,1,1]})
 def test_box(self):
  with self.assertRaises(MathOCRError):normalize({"latex":"x","confidence":1,"box":[]})
if __name__=="__main__":unittest.main()
