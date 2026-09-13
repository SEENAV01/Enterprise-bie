import unittest
from bie.pedagogy.objective_concept_mapping import *
class T(unittest.TestCase):
 def test_link(self): self.assertEqual(validate_link(ObjectiveConceptLink("o","c","PRIMARY",("e",))).concept_id,"c")
