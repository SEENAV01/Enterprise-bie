import unittest
from bie.pedagogy.lesson_duration_estimation import estimate_duration
class T(unittest.TestCase):
 def test_positive(self): self.assertGreater(estimate_duration(2,1,2),0)
