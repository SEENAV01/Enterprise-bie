import unittest
from bie.director.assessment_prompts import *
class T(unittest.TestCase):
    def test_apply(self): self.assertIn("new example",make_assessment_prompt("o","APPLY","charge",["e"]).prompt)
    def test_bad(self):
        with self.assertRaises(ValueError): make_assessment_prompt("o","GUESS","x",["e"])
