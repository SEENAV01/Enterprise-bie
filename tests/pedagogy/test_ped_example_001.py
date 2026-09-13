import unittest
from bie.pedagogy.example_selection import *
class T(unittest.TestCase):
 def test_best_coverage(self): self.assertEqual(select_example([ExampleCandidate('a',('c',),('e',),.5,.9),ExampleCandidate('b',('x',),('e',),.5,1)],['c']).example_id,'a')
 def test_evidence(self):
  with self.assertRaises(ValueError): select_example([ExampleCandidate('a',('c',),(),.5,.9)],['c'])
