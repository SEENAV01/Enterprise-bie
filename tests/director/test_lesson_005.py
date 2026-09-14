import unittest
from bie.director.transition_strategy import *
class T(unittest.TestCase):
    def test_causal(self): self.assertIn("mechanism",plan_transition("a","b","CAUSE").cue)
    def test_self(self):
        with self.assertRaises(ValueError): plan_transition("a","a","DETAIL")
