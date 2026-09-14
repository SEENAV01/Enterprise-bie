import unittest
from bie.director.voiceover_generation import *
class T(unittest.TestCase):
    def test_flag(self):
        r=generate_voiceover("s",["a","b"],{"a":["e"]}); self.assertEqual(r.unsupported_claims,("b",)); self.assertTrue(r.requires_review)
    def test_grounded(self): self.assertEqual(generate_voiceover("s",["a"],{"a":["e"]}).text,"a")
