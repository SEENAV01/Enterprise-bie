
import unittest
from book_intelligence.figure_semantics import *
class T(unittest.TestCase):
 def test_ok(self):self.assertEqual(build("f"," force ",("A","B"),(("A","acts_on","B"),),.9).summary,"force")
 def test_empty(self):
  with self.assertRaises(FigureSemanticError):build("f","",(),(),.9)
 def test_relation(self):
  with self.assertRaises(FigureSemanticError):build("f","x",("A",),(("A","r","B"),),.9)
 def test_conf(self):
  with self.assertRaises(FigureSemanticError):build("f","x",(),(),2)
if __name__=="__main__":unittest.main()
