import unittest
from bie.scene_ir.callout_element import build
class T(unittest.TestCase):
    def test_valid(self): self.assertTrue(build('e','target','hello',('s',),('r',)).element_type == 'callout')
    def test_invalid(self):
        with self.assertRaises(Exception): build('e','target','hello',('s',),('r',),placement='center')
