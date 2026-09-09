import unittest
from app.bie.math_intelligence.crossmodal_math import *
class T(unittest.TestCase):
 def test_graph(self): self.assertEqual(link("e1","g1","graph","plots",.9).modality,"graph")
 def test_targets(self): self.assertEqual(targets([link("e","t","table","defines columns",1)],"table"),("t",))
 def test_bad_mod(self):
  with self.assertRaises(ValueError):link("e","x","audio","r",1)
 def test_conf(self):
  with self.assertRaises(ValueError):link("e","x","graph","r",-1)
if __name__=="__main__":unittest.main()
