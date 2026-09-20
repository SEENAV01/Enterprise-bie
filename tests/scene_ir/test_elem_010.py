import unittest
from bie.scene_ir.image_element import build
class T(unittest.TestCase):
    def test_valid(self): self.assertTrue(build('e','asset://i',('s',),('r',),rights_ref='r',alt_text='alt').element_type == 'image')
    def test_invalid(self):
        with self.assertRaises(Exception): build('e','asset://i',('s',),('r',),rights_ref='',alt_text='alt')
