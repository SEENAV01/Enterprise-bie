import unittest
from dataclasses import replace
from bie.game_engine.errors import GameContractError
from bie.game_engine.handoff_engine.materializer import materialize,to_compiler_context
from bie.game_engine.compiler_engine.pipeline import compile_game
from tests.hardening_h2.support import *
class Tests(unittest.TestCase):
 def test_materializes_valid_document(self):
  m=materialized();self.assertEqual(len(m.document.experiences),1);self.assertTrue(m.document.experiences[0].levels);self.assertFalse(m.product_accepted)
 def test_deterministic(self):self.assertEqual(materialize(materialization_inputs()),materialize(materialization_inputs()))
 def test_text_coverage_fail_closed(self):
  x=materialization_inputs();
  with self.assertRaises(GameContractError):materialize(replace(x,texts={}))
 def test_visual_coverage_fail_closed(self):
  x=materialization_inputs();
  with self.assertRaises(GameContractError):materialize(replace(x,visuals={}))
 def test_document_preserves_plan_objectives(self):
  m=materialized();objs={c.learning.objective_id for l in m.document.experiences[0].levels for c in l.challenges};self.assertEqual(objs,{x.objective_id for x in materialization_inputs().plan.objective_assignments})
 def test_dynamic_has_motion_and_camera(self):
  level=materialized().document.experiences[0].levels[0];self.assertTrue(level.visual.motion);self.assertTrue(level.visual.camera)
 def test_compiler_context_valid(self):self.assertIsNotNone(to_compiler_context(materialized()).validate())
 def test_compiles_materialized_game(self):self.assertGreater(len(compiled().artifacts),10)
 def test_receipt_binds_plan_and_document(self):
  m=materialized();self.assertEqual(m.receipt.plan_fingerprint,materialization_inputs().plan.plan_fingerprint);self.assertEqual(m.receipt.document_fingerprint,m.document.fingerprint())
 def test_no_unresolved_fields(self):self.assertEqual(materialized().receipt.unresolved_fields,())
