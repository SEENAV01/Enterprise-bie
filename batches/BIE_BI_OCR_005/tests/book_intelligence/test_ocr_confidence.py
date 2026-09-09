
import unittest
from book_intelligence.ocr_confidence import *
class T(unittest.TestCase):
 def test_mean(self):self.assertAlmostEqual(summarize([1,.8]).mean,.9)
 def test_review(self):self.assertTrue(summarize([.2,.9]).needs_review)
 def test_ok(self):self.assertFalse(summarize([.9,.9]).needs_review)
 def test_empty(self):
  with self.assertRaises(ConfidenceError):summarize([])
 def test_score(self):
  with self.assertRaises(ConfidenceError):summarize([2])
if __name__=="__main__":unittest.main()
