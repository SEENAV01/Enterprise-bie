import unittest
from bie.scene_ir.model3d_element import build
class T(unittest.TestCase):
    def test_valid(self): self.assertTrue(build('e','asset://m',('s',),('r',),coordinate_frame='world').element_type == 'model3d')
    def test_invalid(self):
        with self.assertRaises(Exception): build('e','m',('s',),('r',),coordinate_frame='w',scale=(1,0,1))
