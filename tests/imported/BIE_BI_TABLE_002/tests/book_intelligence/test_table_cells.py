
import unittest
from bie.document_intelligence.table_cells import *
class T(unittest.TestCase):
 def c(self):return Cell(0,0,"x",.9)
 def test_ok(self):self.assertEqual(len(validate_cells([self.c()],1,1)),1)
 def test_dup(self):
  with self.assertRaises(CellError):validate_cells([self.c(),self.c()],1,1)
 def test_range(self):
  with self.assertRaises(CellError):validate_cells([Cell(1,0,"x",1)],1,1)
 def test_shape(self):
  with self.assertRaises(CellError):validate_cells([],0,1)
 def test_conf(self):
  with self.assertRaises(CellError):validate_cells([Cell(0,0,"x",2)],1,1)
if __name__=="__main__":unittest.main()
