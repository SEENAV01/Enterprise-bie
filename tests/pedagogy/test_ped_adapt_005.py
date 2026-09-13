import unittest
from bie.pedagogy.repetition_policy import repetition_policy
class T(unittest.TestCase):
 def test_error(self): self.assertEqual(repetition_policy(.9,True,2).mode,'TARGETED')
 def test_high(self): self.assertEqual(repetition_policy(.9,True,0).mode,'RETRIEVAL_ONLY')
