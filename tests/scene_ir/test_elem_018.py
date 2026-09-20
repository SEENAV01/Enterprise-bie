import unittest
from bie.scene_ir.particle_system_element import build
class T(unittest.TestCase):
    def test_valid(self): self.assertTrue(build('e',10,('s',),('r',),emitter={'type':'point'}).element_type == 'particle_system')
    def test_invalid(self):
        with self.assertRaises(Exception): build('e',0,('s',),('r',),emitter={})
