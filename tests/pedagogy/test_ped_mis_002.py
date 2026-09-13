import unittest
from bie.pedagogy.misconception_diagnostic import diagnose_misconceptions
class T(unittest.TestCase):
 def test_detect(self): self.assertEqual(diagnose_misconceptions({'s':.9},{'s':('m',)}).suspected_misconceptions,('m',))
 def test_weak(self): self.assertFalse(diagnose_misconceptions({'s':.2},{'s':('m',)}).requires_followup)
