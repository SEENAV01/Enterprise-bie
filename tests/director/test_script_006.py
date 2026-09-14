import unittest
from bie.director.demonstration_narration import *
class T(unittest.TestCase):
    def test_order(self): self.assertEqual([x.phase for x in narrate_demonstration("s","a","o","i",["e"])],["SETUP","ACTION","OBSERVE","INTERPRET"])
