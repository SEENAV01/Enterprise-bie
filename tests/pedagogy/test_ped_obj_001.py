import unittest
from bie.pedagogy.learning_objective_generator import generate_objective
class T(unittest.TestCase):
 def test_grounded(self): self.assertEqual(generate_objective("c","charge",["e"]).concept_id,"c")
 def test_evidence(self):
  with self.assertRaises(ValueError): generate_objective("c","x",[])
