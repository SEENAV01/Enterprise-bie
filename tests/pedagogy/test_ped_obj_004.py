import unittest
from bie.pedagogy.objective_evidence import objective_evidence
class T(unittest.TestCase):
 def test_partial(self): self.assertTrue(objective_evidence(["a","b"],["a"]).requires_review)
