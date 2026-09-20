import unittest
from bie.scene_ir.model2d_element import build
class T(unittest.TestCase):
    def test_valid(self): self.assertTrue(build('e',((0,0),(1,0)),('s',),('r',)).element_type == 'model2d')
    def test_invalid(self):
        with self.assertRaises(Exception): build('e',((0,0),),('s',),('r',))
