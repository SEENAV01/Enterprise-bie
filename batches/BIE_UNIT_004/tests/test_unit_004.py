import unittest
from app.bie.math_intelligence.dimensional_analysis import *
class T(unittest.TestCase):
 def test_velocity(self): self.assertEqual(dimension_of([("m",1),("s",-1)]),Dimension(L=1,T=-1))
 def test_force(self): self.assertEqual(dimension_of([("kg",1),("m",1),("s",-2)]),Dimension(L=1,M=1,T=-2))
 def test_combine(self): self.assertEqual(combine(Dimension(L=1),Dimension(T=1),-1).T,-1)
 def test_bad(self):
  with self.assertRaises(ValueError):dimension_of([("x",1)])
if __name__=="__main__":unittest.main()
