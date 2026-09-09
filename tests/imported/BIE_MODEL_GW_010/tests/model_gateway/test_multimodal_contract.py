
import unittest
from bie.model_gateway.multimodal_contract import *
class T(unittest.TestCase):
 def test_text(self):self.assertEqual(len(validate_parts([Part("text","x")])),1)
 def test_image(self):self.assertEqual(validate_parts([Part("image",b"x","image/png")])[0].kind,"image")
 def test_empty(self):
  with self.assertRaises(MultimodalError):validate_parts([])
 def test_kind(self):
  with self.assertRaises(MultimodalError):validate_parts([Part("3d","x")])
 def test_mime(self):
  with self.assertRaises(MultimodalError):validate_parts([Part("image",b"x")])
if __name__=="__main__":unittest.main()
