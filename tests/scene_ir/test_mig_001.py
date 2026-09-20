import unittest
from bie.scene_ir.legacy_scenedsl_adapter import *
class T(unittest.TestCase):
 def doc(self):
  return {"format":"legacy-scenedsl","scene_id":"s","duration_ms":500,"source_refs":["src"],"reasoning_refs":["r"],
          "nodes":[{"id":"t","type":"Text","props":{"text":"Hello"}}],
          "animations":[{"id":"a","target":"t","action":"reveal","start_ms":0,"end_ms":200}]}
 def test_pass(self):
  d,e=adapt_legacy_scenedsl(self.doc());self.assertEqual(d["schema_version"],"1.0.0");self.assertTrue(require_lossless_lineage(e))
 def test_type_map(self):self.assertEqual(adapt_legacy_scenedsl(self.doc())[0]["elements"][0]["element_type"],"text")
 def test_track(self):self.assertEqual(adapt_legacy_scenedsl(self.doc())[0]["tracks"][0]["element_id"],"t")
 def test_unknown(self):
  x=self.doc();x["nodes"][0]["type"]="Magic"
  with self.assertRaises(DSLMigrationError):adapt_legacy_scenedsl(x)
 def test_lineage(self):
  x=self.doc();x["source_refs"]=[]
  with self.assertRaises(DSLMigrationError):adapt_legacy_scenedsl(x)
 def test_target(self):
  x=self.doc();x["animations"][0]["target"]="missing"
  with self.assertRaises(DSLMigrationError):adapt_legacy_scenedsl(x)
 def test_not_accepted(self):self.assertFalse(adapt_legacy_scenedsl(self.doc())[1].accepted)
