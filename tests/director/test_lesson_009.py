import unittest
from bie.director.curiosity_gaps import *
class T(unittest.TestCase):
    def test_bad(self):
        with self.assertRaises(ValueError): create_curiosity_gap("g","statement","s",["e"])
    def test_valid(self): self.assertEqual(create_curiosity_gap("g","Why?","s",["e"]).gap_id,"g")
