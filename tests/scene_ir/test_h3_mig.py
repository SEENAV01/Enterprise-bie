import unittest
from bie.scene_ir.migration_verification import *
class T(unittest.TestCase):
 def legacy(self):
  return {"format":"legacy-scenedsl","scene_id":"s","duration_ms":100,"source_refs":["src"],"reasoning_refs":["r"],
          "nodes":[{"id":"e","type":"Text","props":{"text":"Hello"}}],
          "animations":[{"id":"t","target":"e","action":"reveal","start_ms":0,"end_ms":100}]}
 def five(self):
  return {"format":"five-pane","scene_id":"s","duration_ms":100,"source_refs":["src"],"reasoning_refs":["r"],
          "panes":{"title":{"content":"Title"},"center":{"content":"Body"}}}
 def test_legacy(self):
  d,r=verify_migration(self.legacy(),"legacy-scenedsl");self.assertTrue(r.passed);self.assertEqual(d.schema_version,"1.0.0")
 def test_five(self):
  d,r=verify_migration(self.five(),"five-pane");self.assertTrue(r.passed);self.assertEqual(len(d.elements),2)
 def test_adapter(self):
  with self.assertRaises(ValueError):verify_migration(self.legacy(),"unknown")
 def test_bad_legacy(self):
  x=self.legacy();x["source_refs"]=[]
  with self.assertRaises(Exception):verify_migration(x,"legacy-scenedsl")
 def test_require(self):
  _,r=verify_migration(self.legacy(),"legacy-scenedsl");self.assertTrue(require_verified_migration(r))
 def test_not_accepted(self):
  _,r=verify_migration(self.legacy(),"legacy-scenedsl");self.assertFalse(r.accepted)
