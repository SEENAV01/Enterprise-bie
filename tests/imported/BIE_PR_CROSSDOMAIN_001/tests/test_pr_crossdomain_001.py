import unittest
from bie.prerequisite_intelligence.cross_domain import *
class T(unittest.TestCase):
 def test_math_for_physics(self): self.assertEqual(detect_cross_domain("resolve the vector into component and magnitude and direction","physics")[0].domain,"vectors")
 def test_calculus(self): self.assertTrue(any(x.domain=="calculus" for x in detect_cross_domain("take derivative rate of change","physics")))
 def test_none(self): self.assertEqual(detect_cross_domain("French Revolution causes","history"),[])
 def test_skip_target(self): self.assertEqual(detect_cross_domain("solve equation","algebra"),[])
if __name__=="__main__": unittest.main()
