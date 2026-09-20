import unittest
from bie.scene_ir.graph_element import build
class T(unittest.TestCase):
    def test_valid(self): self.assertTrue(build('e',({'points':[(0,0),(1,1)]},),('s',),('r',),x_label='x',y_label='y').element_type == 'graph')
    def test_invalid(self):
        with self.assertRaises(Exception): build('e',({'points':[(0,0)]},),('s',),('r',),x_label='x',y_label='y')
