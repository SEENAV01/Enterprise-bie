import unittest
from bie.scene_ir.equation_element import build
class T(unittest.TestCase):
    def test_valid(self): self.assertTrue(build('e','x=1',('s',),('r',)).element_type == 'equation')
    def test_invalid(self):
        with self.assertRaises(Exception): build('e','x',('s',),('r',),format='svg')
