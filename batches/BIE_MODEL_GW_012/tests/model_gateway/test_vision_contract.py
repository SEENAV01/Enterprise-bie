
import unittest
from model_gateway.vision_contract import *
class T(unittest.TestCase):
 def test_ok(self):self.assertTrue(validate(VisionInput("a","image/png",10,10)))
 def test_mime(self):
  with self.assertRaises(VisionError):validate(VisionInput("a","text/plain"))
 def test_ref(self):
  with self.assertRaises(VisionError):validate(VisionInput("","image/png"))
 def test_width(self):
  with self.assertRaises(VisionError):validate(VisionInput("a","image/png",0,1))
 def test_height(self):
  with self.assertRaises(VisionError):validate(VisionInput("a","image/png",1,0))
if __name__=="__main__":unittest.main()
