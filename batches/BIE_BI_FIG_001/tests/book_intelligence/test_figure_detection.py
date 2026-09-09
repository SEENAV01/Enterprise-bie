
import unittest
from book_intelligence.figure_detection import *
class T(unittest.TestCase):
 def f(self):return FigureRegion("f",1,(0,0,1,1),.9)
 def test_ok(self):self.assertEqual(len(normalize([self.f()])),1)
 def test_dup(self):
  with self.assertRaises(FigureError):normalize([self.f(),self.f()])
 def test_page(self):
  with self.assertRaises(FigureError):normalize([FigureRegion("f",0,(0,0,1,1),1)])
 def test_box(self):
  with self.assertRaises(FigureError):normalize([FigureRegion("f",1,(0,0,2,1),1)])
 def test_conf(self):
  with self.assertRaises(FigureError):normalize([FigureRegion("f",1,(0,0,1,1),2)])
if __name__=="__main__":unittest.main()
