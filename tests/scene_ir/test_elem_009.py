import unittest
from bie.scene_ir.timeline_element import build
class T(unittest.TestCase):
    def test_valid(self): self.assertTrue(build('e',({'event_id':'a'},{'event_id':'b'}),('s',),('r',)).element_type == 'timeline')
    def test_invalid(self):
        with self.assertRaises(Exception): build('e',({'event_id':'a'},),('s',),('r',))
