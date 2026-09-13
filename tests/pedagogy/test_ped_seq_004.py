import unittest
from bie.pedagogy.cognitive_load_control import assess_load
class T(unittest.TestCase):
 def test_overload(self): self.assertTrue(assess_load(.8,.7,.6).overload)
