import unittest
from bie.scene_ir.map_element import build
class T(unittest.TestCase):
    def test_valid(self): self.assertTrue(build('e','EPSG:4326',({'layer_id':'l','kind':'route'},),('s',),('r',)).element_type == 'map')
    def test_invalid(self):
        with self.assertRaises(Exception): build('e','EPSG:4326',({'layer_id':'l'},),('s',),('r',))
