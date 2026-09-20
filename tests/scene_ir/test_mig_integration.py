import unittest
from bie.scene_ir.legacy_scenedsl_adapter import adapt_legacy_scenedsl
from bie.scene_ir.five_pane_adapter import adapt_five_pane
from bie.scene_ir.legacy_retirement import *

class T(unittest.TestCase):
 def test_legacy_migration_and_retirement(self):
  legacy={"format":"legacy-scenedsl","scene_id":"s","duration_ms":500,
          "source_refs":["src"],"reasoning_refs":["r"],
          "nodes":[{"id":"t","type":"Text","props":{"text":"Hello"}}],"animations":[]}
  out,ev=adapt_legacy_scenedsl(legacy)
  self.assertEqual(out["schema_version"],"1.0.0")
  self.assertTrue(ev.preserved_source_refs and ev.preserved_reasoning_refs and not ev.lossy)
  p=default_retirement_policies()[0]
  self.assertEqual(evaluate_legacy_use(p,operation="import",has_migration_evidence=True).action,"MIGRATE")

 def test_five_pane_generic_ir(self):
  old={"format":"five-pane","scene_id":"s","source_refs":["src"],"reasoning_refs":["r"],
       "panes":{"title":{"content":"Title"},"center":{"content":"Body"}}}
  out,_=adapt_five_pane(old)
  self.assertEqual(out["metadata"]["migrated_from"],"five-pane")
  self.assertEqual(len(out["elements"]),2)

 def test_legacy_write_retired(self):
  self.assertTrue(all(evaluate_legacy_use(p,operation="write").action=="BLOCK" for p in default_retirement_policies()))
