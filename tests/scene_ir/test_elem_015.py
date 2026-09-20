import unittest
from bie.scene_ir.annotation_element import build
class T(unittest.TestCase):
    def test_valid(self): self.assertTrue(build('e','target','note',('s',),('r',)).element_type == 'annotation')
    def test_invalid(self):
        with self.assertRaises(Exception): build('e','','note',('s',),('r',))
