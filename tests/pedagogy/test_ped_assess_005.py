import unittest
from bie.pedagogy.mastery_checks import evaluate_mastery
class T(unittest.TestCase):
 def test_transfer(self): self.assertFalse(evaluate_mastery('o',.9,False,2).mastered)
 def test_mastered(self): self.assertTrue(evaluate_mastery('o',.9,True,2).mastered)
