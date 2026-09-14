import unittest
from bie.director.derivation_narration import *
class T(unittest.TestCase):
    def test_steps(self): self.assertTrue(narrate_derivation([("a=b","given",("e",)),("b=c","sub",("e",))])[1].narration.startswith("Step 2"))
