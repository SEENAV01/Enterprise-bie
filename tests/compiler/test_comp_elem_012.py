import unittest
from bie.compiler.annotation_callout_compiler import *
class T(unittest.TestCase):
 def a(self):return {"element_id":"a","element_type":"annotation","props":{"target_element_id":"x","text":"note"},"accessibility":{},"source_refs":["s"],"reasoning_refs":["r"]}
 def c(self):return {"element_id":"c","element_type":"callout","props":{"target_element_id":"x","content":"important"},"accessibility":{},"source_refs":["s"],"reasoning_refs":["r"]}
 def test_annotation(self):self.assertIn("note",compile_annotation_callout_element(self.a()).source_text)
 def test_callout(self):self.assertIn("important",compile_annotation_callout_element(self.c()).source_text)
 def test_target(self):self.assertIn("data-target-element-id",compile_annotation_callout_element(self.a()).source_text)
 def test_missing(self):
  x=self.a();x["props"]["target_element_id"]=""
  with self.assertRaises(ElementCompilerError):compile_annotation_callout_element(x)
 def test_type(self):
  x=self.a();x["element_type"]="text"
  with self.assertRaises(ElementCompilerError):compile_annotation_callout_element(x)
