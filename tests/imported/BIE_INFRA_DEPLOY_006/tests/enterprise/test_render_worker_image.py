
import unittest
from bie.infrastructure.render_worker_image import *
class T(unittest.TestCase):
 def m(self):return {"tools":["node","remotion","ffmpeg","chromium"],"fonts_pinned":True,"gpu_optional":True}
 def test_ok(self):self.assertTrue(validate_manifest(self.m()))
 def test_tool(self):
  x=self.m();x["tools"].remove("ffmpeg")
  with self.assertRaises(RenderImageError):validate_manifest(x)
 def test_fonts(self):
  x=self.m();x["fonts_pinned"]=False
  with self.assertRaises(RenderImageError):validate_manifest(x)
 def test_gpu_decl(self):
  x=self.m();x["gpu_optional"]=False
  with self.assertRaises(RenderImageError):validate_manifest(x)
if __name__=="__main__":unittest.main()
