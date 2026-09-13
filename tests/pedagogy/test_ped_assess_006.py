import unittest
from bie.pedagogy.assessment_difficulty import estimate_assessment_difficulty
class T(unittest.TestCase):
 def test_scaffold(self): self.assertLess(estimate_assessment_difficulty(4,.7,5,.9).score,estimate_assessment_difficulty(4,.7,5,.1).score)
