import unittest
from bie.director.socratic_dialogue import *
class T(unittest.TestCase):
    def test_challenge(self): self.assertIn("CHALLENGE",[x.kind for x in socratic_sequence("c","claim",["e"],"wrong")])
    def test_elicit(self): self.assertEqual(socratic_sequence("c","claim",["e"])[0].kind,"ELICIT")
