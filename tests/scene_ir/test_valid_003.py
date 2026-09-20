import unittest
from bie.scene_ir.reference_validation import *
class T(unittest.TestCase):
 def test_pass(self):
  d={"elements":[{"element_id":"e","element_type":"text","props":{}}],"tracks":[{"track_id":"t","element_id":"e"}]}
  self.assertTrue(validate_references(d).passed)
 def test_unknown_track(self):
  d={"elements":[{"element_id":"e","element_type":"text","props":{}}],"tracks":[{"track_id":"t","element_id":"x"}]}
  self.assertFalse(validate_references(d).passed)
 def test_dup_element(self):
  d={"elements":[{"element_id":"e","element_type":"text","props":{}},{"element_id":"e","element_type":"text","props":{}}],"tracks":[]}
  self.assertFalse(validate_references(d).passed)
 def test_annotation(self):
  d={"elements":[{"element_id":"a","element_type":"annotation","props":{"target_element_id":"x"}}],"tracks":[]}
  self.assertFalse(validate_references(d).passed)
 def test_highlight(self):
  d={"elements":[{"element_id":"h","element_type":"highlight","props":{"target_element_ids":["x"]}}],"tracks":[]}
  self.assertFalse(validate_references(d).passed)
 def test_not_accepted(self):self.assertFalse(validate_references({"elements":[],"tracks":[]}).accepted)
