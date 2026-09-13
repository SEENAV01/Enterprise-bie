import unittest
from bie.pedagogy.example_difficulty import estimate_example_difficulty
class T(unittest.TestCase):
 def test_order(self):
  a=estimate_example_difficulty(2,.1,.1,.1,.1); b=estimate_example_difficulty(9,.9,.8,.9,.8); self.assertGreater(b.score,a.score)
