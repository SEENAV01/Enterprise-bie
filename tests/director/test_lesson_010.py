import unittest
from bie.director.payoff_structure import *
class T(unittest.TestCase):
    def test_unresolved(self):
        with self.assertRaises(ValueError): bind_payoffs([("g",("e",))],{})
    def test_merge(self): self.assertEqual(bind_payoffs([("g",("e1",))],{"g":("s","answer",("e2",))})[0].evidence_ids,("e1","e2"))
