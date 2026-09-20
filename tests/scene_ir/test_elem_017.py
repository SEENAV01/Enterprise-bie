import unittest
from bie.scene_ir.highlight_element import build
class T(unittest.TestCase):
    def test_valid(self): self.assertTrue(build('e',('a','b'),('s',),('r',)).element_type == 'highlight')
    def test_invalid(self):
        with self.assertRaises(Exception): build('e',('a','a'),('s',),('r',))
