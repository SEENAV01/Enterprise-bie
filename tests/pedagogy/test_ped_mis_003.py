import unittest
from bie.pedagogy.misconception_remediation import plan_misconception_remediation
class T(unittest.TestCase):
 def test_transfer(self): self.assertIn('independent transfer check',plan_misconception_remediation('m','model',['e']).sequence)
