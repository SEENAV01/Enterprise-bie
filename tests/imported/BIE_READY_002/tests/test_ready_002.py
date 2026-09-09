import unittest
from app.bie.readiness_intelligence.thresholds import *
class T(unittest.TestCase):
 def test_base(self): self.assertEqual(readiness_threshold().value,.75)
 def test_critical(self): self.assertGreater(readiness_threshold(criticality=1).value,.75)
 def test_support(self): self.assertLess(readiness_threshold(support_available=1).value,.75)
 def test_invalid(self):
  with self.assertRaises(ValueError): readiness_threshold(base=2)
if __name__=="__main__": unittest.main()
