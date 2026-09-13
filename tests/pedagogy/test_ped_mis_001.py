import unittest
from bie.pedagogy.misconception_confrontation import plan_confrontation
class T(unittest.TestCase):
 def test_grounded(self): self.assertEqual(plan_confrontation('m','x','demo','model',['e']).misconception_id,'m')
 def test_evidence(self):
  with self.assertRaises(ValueError): plan_confrontation('m','x','d','r',[])
