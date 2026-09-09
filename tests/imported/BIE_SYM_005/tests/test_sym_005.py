import unittest
from app.bie.math_intelligence.equation_linkage import *
class T(unittest.TestCase):
 def test_symbols(self): self.assertEqual(link_equation("e1","F = m a","p2").symbols,("F","a","m"))
 def test_unique(self): self.assertEqual(link_equation("e","x+x=y","p").symbols,("x","y"))
 def test_lookup(self):
  l=[link_equation("e1","F=ma","p")];self.assertEqual(equations_for("F",l),("e1",))
 def test_required(self):
  with self.assertRaises(ValueError):link_equation("","x=y","p")
if __name__=="__main__":unittest.main()
