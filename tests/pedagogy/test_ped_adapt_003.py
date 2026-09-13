import unittest
from bie.pedagogy.remediation_path import choose_remediation_path
class T(unittest.TestCase):
 def test_bridge(self): self.assertTrue(choose_remediation_path('c',.3,{'p':.2},False).actions[0].startswith('bridge prerequisites'))
 def test_mis(self): self.assertIn('misconception remediation',choose_remediation_path('c',.5,{},True).actions)
