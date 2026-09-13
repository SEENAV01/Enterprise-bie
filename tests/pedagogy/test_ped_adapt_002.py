import unittest
from bie.pedagogy.mastery_state import update_mastery
class T(unittest.TestCase):
 def test_update(self):
  r=update_mastery('c',.2,.8,'e'); self.assertGreater(r.updated,.2); self.assertLess(r.updated,.8)
