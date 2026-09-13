import unittest
from bie.pedagogy.objective_mastery_criterion import *
class T(unittest.TestCase):
 def test_transfer(self): self.assertFalse(mastery_met(MasteryCriterion(),.9,2,False))
