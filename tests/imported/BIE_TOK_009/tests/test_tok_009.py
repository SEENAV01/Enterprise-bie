import unittest
from bie.math_intelligence.matrices import *
class T(unittest.TestCase):
 def test_shape(self): self.assertEqual((parse_matrix("[1,2;3,4]").nrows,parse_matrix("[1,2;3,4]").ncols),(2,2))
 def test_values(self): self.assertEqual(parse_matrix("[a,b]").rows[0],("a","b"))
 def test_empty(self): self.assertIsNone(parse_matrix(""))
 def test_ragged(self):
  with self.assertRaises(ValueError):parse_matrix("[1,2;3]")
if __name__=="__main__":unittest.main()
