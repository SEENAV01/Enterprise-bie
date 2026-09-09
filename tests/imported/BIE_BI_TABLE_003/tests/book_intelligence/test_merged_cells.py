
import unittest
from bie.document_intelligence.merged_cells import *
class T(unittest.TestCase):
 def test_ok(self):self.assertEqual(len(validate_spans([Span(0,0,1,2)],1,2)),1)
 def test_bounds(self):
  with self.assertRaises(MergeError):validate_spans([Span(0,0,2,1)],1,1)
 def test_zero(self):
  with self.assertRaises(MergeError):validate_spans([Span(0,0,0,1)],1,1)
 def test_overlap(self):
  with self.assertRaises(MergeError):validate_spans([Span(0,0,1,2),Span(0,1,1,1)],1,2)
if __name__=="__main__":unittest.main()
