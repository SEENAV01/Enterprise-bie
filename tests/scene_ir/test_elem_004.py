import unittest
from bie.scene_ir.vector_element import build
class T(unittest.TestCase):
    def test_valid(self): self.assertTrue(round(build('e',(3,4),('s',),('r',)).props['magnitude'],6) == 5)
    def test_invalid(self):
        with self.assertRaises(Exception): build('e',(1,),('s',),('r',))
