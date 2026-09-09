
import unittest
from book_intelligence.margin_notes import *
class T(unittest.TestCase):
 def test_left(self):self.assertEqual(classify((0,0,10,1),100,20,80),"LEFT_MARGIN")
 def test_right(self):self.assertEqual(classify((90,0,100,1),100,20,80),"RIGHT_MARGIN")
 def test_main(self):self.assertEqual(classify((30,0,60,1),100,20,80),"MAIN_FLOW")
 def test_overlap(self):self.assertEqual(classify((10,0,30,1),100,20,80),"MAIN_FLOW")
 def test_bad(self):
  with self.assertRaises(MarginNoteError):classify((10,0,5,1),100,20,80)
if __name__=="__main__":unittest.main()
