import unittest
from bie.director.misconception_dialogue import *
class T(unittest.TestCase):
    def test_transfer(self): self.assertIn("different example",build_misconception_dialogue("m","counter","model",["e"]).transfer_check)
