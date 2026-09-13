import unittest
from bie.pedagogy.learner_profile_contract import make_learner_profile
class T(unittest.TestCase):
 def test_order(self): self.assertEqual(make_learner_profile('u',{'b':.2,'a':.8}).mastery,(('a',.8),('b',.2)))
 def test_bad(self):
  with self.assertRaises(ValueError): make_learner_profile('u',{'a':1.2})
