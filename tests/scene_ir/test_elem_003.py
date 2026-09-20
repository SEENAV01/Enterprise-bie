import unittest
from bie.scene_ir.shape_element import build
class T(unittest.TestCase):
    def test_valid(self): self.assertTrue(build('e','rectangle',('s',),('r',),geometry={}).element_type == 'shape')
    def test_invalid(self):
        with self.assertRaises(Exception): build('e','polygon',('s',),('r',),geometry={'points':[(0,0),(1,0)]})
