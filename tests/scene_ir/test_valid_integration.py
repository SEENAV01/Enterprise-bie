import unittest
from bie.scene_ir.schema_validation import validate_schema_shape
from bie.scene_ir.semantic_validation import validate_semantics
from bie.scene_ir.reference_validation import validate_references
from bie.scene_ir.temporal_validation import validate_temporal
from bie.scene_ir.spatial_validation import validate_spatial
from bie.scene_ir.accessibility_validation import validate_accessibility
from bie.scene_ir.trace_validation import validate_source_reasoning_trace

class T(unittest.TestCase):
 def good(self):
  return {
   "scene_id":"s","schema_version":"1.0.0","title":"Example","duration_ms":100,
   "source_refs":["src"],"reasoning_refs":["r"],
   "elements":[{"element_id":"e","element_type":"text","props":{"text":"x"},
                "accessibility":{},"source_refs":["src"],"reasoning_refs":["r"]}],
   "tracks":[{"track_id":"t","element_id":"e","action":"reveal","start_ms":0,"end_ms":100,
              "source_refs":["src"],"reasoning_refs":["r"]}],
   "layout":{"boxes":[{"x":0.1,"y":0.1,"width":0.5,"height":0.5}]}
  }

 def test_all_validators_pass_clean_scene(self):
  d=self.good()
  reports=[
   validate_schema_shape(d), validate_semantics(d), validate_references(d),
   validate_temporal(d), validate_spatial(d), validate_accessibility(d),
   validate_source_reasoning_trace(d)
  ]
  self.assertTrue(all(r.passed for r in reports))
  self.assertTrue(all(not r.accepted for r in reports))

 def test_mutation_is_owned_by_correct_validator(self):
  d=self.good()
  d["tracks"][0]["element_id"]="missing"
  self.assertFalse(validate_references(d).passed)
  self.assertTrue(validate_schema_shape(d).passed)

 def test_trace_mutation(self):
  d=self.good()
  d["tracks"][0]["source_refs"]=[]
  self.assertFalse(validate_source_reasoning_trace(d).passed)
