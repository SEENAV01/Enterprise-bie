import unittest
from bie.pedagogy.learner_choice_branches import *
class T(unittest.TestCase):
 def test_filter(self): self.assertEqual([x.branch_id for x in available_choice_branches([ChoiceBranch('a','review',.2,'REVIEW'),ChoiceBranch('b','deep',.9,'DEEP_DIVE')],.5)],['a'])
