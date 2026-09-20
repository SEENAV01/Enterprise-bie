import unittest
from bie.compiler.media_compiler import *
class T(unittest.TestCase):
 def img(self):return {"element_id":"i","element_type":"image","props":{"resolved_asset_path":"images/cell.png"},"accessibility":{},"source_refs":["s"],"reasoning_refs":["r"]}
 def vid(self):return {"element_id":"v","element_type":"video","props":{"resolved_asset_path":"video/demo.mp4"},"accessibility":{},"source_refs":["s"],"reasoning_refs":["r"]}
 def test_image(self):self.assertIn("CanvasImage",compile_image_or_video_element(self.img()).source_text)
 def test_video(self):self.assertIn("@remotion/media",compile_image_or_video_element(self.vid()).source_text)
 def test_staticfile(self):self.assertIn("staticFile",compile_image_or_video_element(self.img()).source_text)
 def test_asset(self):self.assertEqual(compile_image_or_video_element(self.img()).asset_paths,("images/cell.png",))
 def test_unresolved(self):
  x=self.img();x["props"]={"asset_ref":"asset://x"}
  with self.assertRaises(ElementCompilerError):compile_image_or_video_element(x)
 def test_url_block(self):
  x=self.img();x["props"]["resolved_asset_path"]="https://x"
  with self.assertRaises(ElementCompilerError):compile_image_or_video_element(x)
