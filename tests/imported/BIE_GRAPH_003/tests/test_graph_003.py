import unittest
from app.bie.math_intelligence.transformations import *
class T(unittest.TestCase):
 def test_shift(self): self.assertEqual(transformations(h=2)[0].kind,"horizontal_shift")
 def test_reflect(self): self.assertEqual(transformations(a=-1)[0].kind,"reflection_x")
 def test_scale(self): self.assertTrue(any(x.kind=="vertical_scale" for x in transformations(a=3)))
 def test_identity(self): self.assertEqual(transformations(),())
if __name__=="__main__":unittest.main()
