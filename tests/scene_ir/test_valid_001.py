import unittest
from bie.scene_ir.schema_validation import *
class T(unittest.TestCase):
 def base(self):return {"scene_id":"s","schema_version":"1.0.0","title":"x","duration_ms":100,"elements":[{"element_id":"e"}],"tracks":[],"source_refs":["s"],"reasoning_refs":["r"]}
 def test_pass(self):self.assertTrue(validate_schema_shape(self.base()).passed)
 def test_missing(self):
  d=self.base();d.pop("title");self.assertFalse(validate_schema_shape(d).passed)
 def test_version(self):
  d=self.base();d["schema_version"]="2.0.0";self.assertFalse(validate_schema_shape(d).passed)
 def test_duration(self):
  d=self.base();d["duration_ms"]=0;self.assertFalse(validate_schema_shape(d).passed)
 def test_root(self):self.assertFalse(validate_schema_shape([]).passed)
 def test_not_accepted(self):self.assertFalse(validate_schema_shape(self.base()).accepted)
