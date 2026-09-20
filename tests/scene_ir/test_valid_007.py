import unittest
from bie.scene_ir.trace_validation import *
class T(unittest.TestCase):
 def good(self):return {"source_refs":["s"],"reasoning_refs":["r"],"elements":[{"source_refs":["s"],"reasoning_refs":["r"]}],"tracks":[{"source_refs":["s"],"reasoning_refs":["r"]}]}
 def test_pass(self):self.assertTrue(validate_source_reasoning_trace(self.good()).passed)
 def test_scene_source(self):
  d=self.good();d["source_refs"]=[];self.assertFalse(validate_source_reasoning_trace(d).passed)
 def test_scene_reason(self):
  d=self.good();d["reasoning_refs"]=[];self.assertFalse(validate_source_reasoning_trace(d).passed)
 def test_element(self):
  d=self.good();d["elements"][0]["source_refs"]=[];self.assertFalse(validate_source_reasoning_trace(d).passed)
 def test_track(self):
  d=self.good();d["tracks"][0]["reasoning_refs"]=[];self.assertFalse(validate_source_reasoning_trace(d).passed)
 def test_not_accepted(self):self.assertFalse(validate_source_reasoning_trace(self.good()).accepted)
