import unittest
from bie.compiler.text_compiler import *
class T(unittest.TestCase):
 def e(self):return {"element_id":"t","element_type":"text","props":{"text":"Hello","role":"heading"},"accessibility":{},"source_refs":["s"],"reasoning_refs":["r"]}
 def test_type(self):self.assertEqual(compile_text_element(self.e()).element_type,"text")
 def test_interactive(self):self.assertIn("Interactive.Div",compile_text_element(self.e()).source_text)
 def test_label(self):self.assertIn('aria-label={"Hello"}',compile_text_element(self.e()).source_text)
 def test_wrong(self):
  x=self.e();x["element_type"]="map"
  with self.assertRaises(ElementCompilerError):compile_text_element(x)
 def test_lineage(self):
  x=self.e();x["source_refs"]=[]
  with self.assertRaises(ElementCompilerError):compile_text_element(x)
