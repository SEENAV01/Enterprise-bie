import unittest
from bie.scene_ir.video_element import build
class T(unittest.TestCase):
    def test_valid(self): self.assertTrue(build('e','asset://v',('s',),('r',),rights_ref='r').element_type == 'video')
    def test_invalid(self):
        with self.assertRaises(Exception): build('e','asset://v',('s',),('r',),rights_ref='r',trim_start_ms=100,trim_end_ms=50)
