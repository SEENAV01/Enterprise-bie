
import unittest
from book_intelligence.figure_provenance import *
class T(unittest.TestCase):
 def p(self):return FigureProvenance("f","a"*64,1,(0,0,1,1),"cas:x")
 def test_ok(self):self.assertTrue(validate(self.p()))
 def test_hash(self):
  with self.assertRaises(FigureProvError):validate(FigureProvenance("f","x",1,(0,0,1,1),"a"))
 def test_page(self):
  with self.assertRaises(FigureProvError):validate(FigureProvenance("f","a"*64,0,(0,0,1,1),"a"))
 def test_ref(self):
  with self.assertRaises(FigureProvError):validate(FigureProvenance("f","a"*64,1,(0,0,1,1),""))
if __name__=="__main__":unittest.main()
