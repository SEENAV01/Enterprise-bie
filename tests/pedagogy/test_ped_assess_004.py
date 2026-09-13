import unittest
from bie.pedagogy.diagnostic_checks import make_diagnostic_check
class T(unittest.TestCase):
 def test_map(self): self.assertEqual(make_diagnostic_check('q',['m1'],{'B':'m1'},['e']).distractor_map,(('B','m1'),))
