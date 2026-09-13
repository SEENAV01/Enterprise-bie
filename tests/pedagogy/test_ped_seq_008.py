import unittest
from bie.pedagogy.review_spacing import review_schedule
class T(unittest.TestCase):
 def test_low_sooner(self): self.assertLess(review_schedule(10,.4)[0],review_schedule(10,.9)[0])
