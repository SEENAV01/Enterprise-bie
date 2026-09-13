import unittest
from bie.pedagogy.acceleration_path import choose_acceleration_path
class T(unittest.TestCase):
 def test_yes(self): self.assertTrue(choose_acceleration_path(.9,.9,.9).eligible)
 def test_transfer_blocks(self): self.assertFalse(choose_acceleration_path(.95,.6,.95).eligible)
