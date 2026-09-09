import unittest
from bie.reasoning.causal_mechanism import *
class T(unittest.TestCase):
 def test_valid(self):self.assertTrue(validate(Mechanism("A","M","B",("e",),.9)))
 def test_evidence(self):
  with self.assertRaises(ValueError):validate(Mechanism("A","M","B",(),.9))
 def test_distinct(self):
  with self.assertRaises(ValueError):validate(Mechanism("A","A","B",("e",),.9))
 def test_conf(self):
  with self.assertRaises(ValueError):validate(Mechanism("A","M","B",("e",),2))
