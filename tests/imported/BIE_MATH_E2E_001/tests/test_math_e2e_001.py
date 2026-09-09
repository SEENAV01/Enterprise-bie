import unittest
from bie.math_intelligence.math_pipeline import *
class T(unittest.TestCase):
 def test_pipeline(self):
  a=process_math("F = m*a","p12:eq1");self.assertEqual((a.relation,a.symbols),("=",("F","a","m")))
 def test_provenance(self):
  with self.assertRaises(ValueError):process_math("x=1","")
 def test_delimiter(self): self.assertIn("delimiter_error",process_math("(x=1","p").qa)
 def test_no_relation(self): self.assertIn("no_relation",process_math("x+1","p").qa)
if __name__=="__main__":unittest.main()
