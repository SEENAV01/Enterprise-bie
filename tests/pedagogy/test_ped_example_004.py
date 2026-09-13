import unittest
from bie.pedagogy.counterexample_selection import *
class T(unittest.TestCase):
 def test_match(self): self.assertEqual(select_counterexample([Counterexample('x',('m',),('c',),('e',),.8)],'m','c').counterexample_id,'x')
 def test_none(self):
  with self.assertRaises(ValueError): select_counterexample([],'m','c')
