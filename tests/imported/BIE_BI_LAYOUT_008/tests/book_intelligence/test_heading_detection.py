
import unittest
from bie.document_intelligence.heading_detection import *
class T(unittest.TestCase):
 def test_high(self):self.assertTrue(is_heading({"font_scale":1,"bold":1,"spacing_before":1,"spacing_after":1,"shortness":1,"numbering":1}))
 def test_low(self):self.assertFalse(is_heading({}))
 def test_score(self):self.assertGreater(heading_score({"font_scale":1}),0)
 def test_feature(self):
  with self.assertRaises(HeadingError):heading_score({"bold":2})
 def test_threshold(self):
  with self.assertRaises(HeadingError):is_heading({},2)
if __name__=="__main__":unittest.main()
