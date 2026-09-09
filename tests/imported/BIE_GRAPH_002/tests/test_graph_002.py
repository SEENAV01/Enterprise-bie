import unittest
from app.bie.math_intelligence.domain_range import *
class T(unittest.TestCase):
 def test_contains(self): self.assertTrue(contains(Interval(0,1,True,False),0))
 def test_open(self): self.assertFalse(contains(Interval(0,1),0))
 def test_infinite(self): self.assertTrue(contains(Interval(None,0),-100))
 def test_bad(self):
  with self.assertRaises(ValueError):validate_interval(Interval(2,1))
if __name__=="__main__":unittest.main()
