import unittest
from bie.director.persona_selection import *
class T(unittest.TestCase):
    def test_derivation(self): self.assertEqual(select_persona("SECONDARY","QUANTITATIVE","DERIVATION").persona,"EXPERT_TUTOR")
    def test_source(self): self.assertEqual(select_persona("ADULT","SOURCE_CRITICISM","EXPLANATION").persona,"DOCUMENTARY_NARRATOR")
