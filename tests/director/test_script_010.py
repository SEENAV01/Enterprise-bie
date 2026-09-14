import unittest
from bie.director.game_handoff import *
class T(unittest.TestCase):
    def test_contract(self): self.assertTrue(build_game_handoff("l",["o"],["c"],["m"],["check"],["e"]).forbidden_ungrounded_mechanics)
    def test_mastery(self):
        with self.assertRaises(ValueError): build_game_handoff("l",["o"],["c"],[],[],["e"])
