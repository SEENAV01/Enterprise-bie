import unittest
from bie.compiler.captions_compiler import *
class T(unittest.TestCase):
 def c(self):return [{"text":"Hello","startMs":0,"endMs":1000,"timestampMs":None,"confidence":0.9},{"text":"World","startMs":1000,"endMs":2000,"timestampMs":None,"confidence":None}]
 def test_type(self):self.assertIn("Caption[]",compile_captions(self.c())[0].content)
 def test_frame(self):self.assertIn("useCurrentFrame()",compile_captions(self.c())[0].content)
 def test_dependency(self):self.assertEqual(compile_captions(self.c())[0].required_dependencies,("@remotion/captions",))
 def test_shape(self):self.assertEqual(set(compile_captions(self.c())[1][0]),{"text","startMs","endMs","timestampMs","confidence"})
 def test_bad_range(self):
  with self.assertRaises(AudioCompilerError):normalize_caption({"text":"x","startMs":10,"endMs":5})
 def test_bad_confidence(self):
  with self.assertRaises(AudioCompilerError):normalize_caption({"text":"x","startMs":0,"endMs":10,"confidence":2})
