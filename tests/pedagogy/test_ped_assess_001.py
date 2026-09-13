import unittest
from bie.pedagogy.formative_checks import make_formative_check
class T(unittest.TestCase):
 def test_grounded(self): self.assertEqual(make_formative_check('q','o','p?','correct',['e']).objective_id,'o')
