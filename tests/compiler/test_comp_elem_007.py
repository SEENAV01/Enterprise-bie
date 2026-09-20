import unittest
from bie.compiler.timeline_compiler import *
class T(unittest.TestCase):
 def e(self):return {"element_id":"tl","element_type":"timeline","props":{"events":[{"event_id":"a","label":"A"},{"event_id":"b","label":"B"}]},"accessibility":{},"source_refs":["s"],"reasoning_refs":["r"]}
 def test_events(self):self.assertIn("const events",compile_timeline_element(self.e()).source_text)
 def test_line(self):self.assertIn("height: 2",compile_timeline_element(self.e()).source_text)
 def test_role(self):self.assertIn('role="img"',compile_timeline_element(self.e()).source_text)
 def test_short(self):
  x=self.e();x["props"]["events"]=[{"event_id":"a"}]
  with self.assertRaises(ElementCompilerError):compile_timeline_element(x)
 def test_hash(self):self.assertEqual(len(compile_timeline_element(self.e()).source_sha256),64)
