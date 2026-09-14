import unittest
from bie.director.hook_strategy import *
class T(unittest.TestCase):
    def test_misconception(self): self.assertEqual(choose_hook("CAUSAL","APPLY",["e"],True).strategy,"PREDICTION_CONFLICT")
    def test_source(self): self.assertEqual(choose_hook("SOURCE_CRITICISM","EVALUATE",["e"]).strategy,"EVIDENCE_MYSTERY")
