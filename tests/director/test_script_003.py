import unittest
from bie.director.dialogue_generation import *
class T(unittest.TestCase):
    def test_ok(self): self.assertEqual(len(build_dialogue([("T","Why?",("e",),"probe"),("L","Because",("e",),"respond")])),2)
    def test_repeat(self):
        with self.assertRaises(ValueError): build_dialogue([("T","a",("e",),"x"),("T","b",("e",),"y")])
