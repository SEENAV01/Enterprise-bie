
import unittest
from book_intelligence.callout_detection import *
class T(unittest.TestCase):
 def test_high(self):self.assertEqual(classify({"border":1,"fill":1,"label":1,"isolation":1}),"CALLOUT_HIGH")
 def test_possible(self):self.assertEqual(classify({"border":1,"fill":1}),"CALLOUT_POSSIBLE")
 def test_main(self):self.assertEqual(classify({}),"MAIN_CONTENT")
 def test_bad(self):
  with self.assertRaises(CalloutError):classify({"border":2})
if __name__=="__main__":unittest.main()
