
import unittest
from bie.document_intelligence.footnote_detection import *
class T(unittest.TestCase):
 def test_link(self):self.assertEqual(link_footnotes([{"id":"m1","marker":"1"}],[{"id":"n1","marker":"1"}]),(("m1","n1"),))
 def test_two(self):self.assertEqual(len(link_footnotes([{"id":"m1","marker":"1"},{"id":"m2","marker":"2"}],[{"id":"n1","marker":"1"},{"id":"n2","marker":"2"}])),2)
 def test_missing(self):
  with self.assertRaises(FootnoteError):link_footnotes([{"id":"m","marker":"1"}],[])
 def test_empty(self):self.assertEqual(link_footnotes([],[]),())
 def test_dup(self):
  with self.assertRaises(FootnoteError):link_footnotes([{"id":"m","marker":"1"},{"id":"m","marker":"1"}],[{"id":"n","marker":"1"}])
if __name__=="__main__":unittest.main()
