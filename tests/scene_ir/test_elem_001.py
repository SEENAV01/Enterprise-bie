import unittest
from bie.scene_ir.text_element import build
class T(unittest.TestCase):
    def test_valid(self): self.assertTrue(build('e','hello',('s',),('r',)).element_type == 'text')
    def test_invalid(self):
        with self.assertRaises(Exception): build('e','x',('s',),('r',),role='bad')
