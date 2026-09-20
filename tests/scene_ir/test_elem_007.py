import unittest
from bie.scene_ir.chart_element import build
class T(unittest.TestCase):
    def test_valid(self): self.assertTrue(build('e','bar',('A','B'),(1,2),('s',),('r',)).element_type == 'chart')
    def test_invalid(self):
        with self.assertRaises(Exception): build('e','bar',('A',),(1,2),('s',),('r',))
