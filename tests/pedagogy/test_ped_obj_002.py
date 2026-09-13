import unittest
from bie.pedagogy.objective_taxonomy import taxonomy_rank
class T(unittest.TestCase):
 def test_order(self): self.assertLess(taxonomy_rank("UNDERSTAND"),taxonomy_rank("APPLY"))
