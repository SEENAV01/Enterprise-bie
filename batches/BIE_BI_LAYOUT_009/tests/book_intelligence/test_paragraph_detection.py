
import unittest
from book_intelligence.paragraph_detection import *
class T(unittest.TestCase):
 def test_one(self):
  l=[{"top":0,"bottom":1,"indent":0},{"top":1.2,"bottom":2,"indent":0}]
  self.assertEqual(len(group_lines(l)),1)
 def test_gap(self):
  l=[{"top":0,"bottom":1,"indent":0},{"top":3,"bottom":4,"indent":0}]
  self.assertEqual(len(group_lines(l)),2)
 def test_indent(self):
  l=[{"top":0,"bottom":1,"indent":0},{"top":1.2,"bottom":2,"indent":.2}]
  self.assertEqual(len(group_lines(l)),2)
 def test_empty(self):self.assertEqual(group_lines([]),())
 def test_bad(self):
  with self.assertRaises(ParagraphError):group_lines([],0)
if __name__=="__main__":unittest.main()
