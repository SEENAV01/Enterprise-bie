import unittest
from bie.notation_intelligence.coordinates import *
class T(unittest.TestCase):
 def test_xy(self): self.assertEqual(infer_coordinate_system({"x","y"}).kind,"cartesian")
 def test_xyz(self): self.assertEqual(infer_coordinate_system({"x","y","z"}).dimensions,3)
 def test_polar(self): self.assertEqual(infer_coordinate_system({"r","θ"}).kind,"polar")
 def test_context(self): self.assertEqual(infer_coordinate_system(set(),"spherical coordinates").kind,"spherical")
if __name__=="__main__": unittest.main()
