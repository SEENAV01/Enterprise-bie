import unittest
from bie.scene_ir.diagram_element import build
class T(unittest.TestCase):
    def test_valid(self): self.assertTrue(build('e',({'node_id':'a'},{'node_id':'b'}),({'from':'a','to':'b'},),('s',),('r',)).element_type == 'diagram')
    def test_invalid(self):
        with self.assertRaises(Exception): build('e',({'node_id':'a'},),({'from':'a','to':'x'},),('s',),('r',))
