import unittest
from bie.scene_ir.dsl_computed_benchmark import *
class T(unittest.TestCase):
 def a(self,**kw):
  d=dict(artifact_id="a",expected_element_types=("text",),produced_element_types=("text",),expected_actions=("reveal",),produced_actions=("reveal",),validation_blockers=(),provenance_passed=True,asset_passed=True,integrity_passed=True,compiler_ready=True);d.update(kw);return DSLBenchmarkArtifact(**d)
 def test_pass(self):self.assertEqual(run_dsl_benchmark([self.a()]).status,"PASS")
 def test_score(self):self.assertEqual(run_dsl_benchmark([self.a()]).score,1.0)
 def test_fail(self):self.assertEqual(run_dsl_benchmark([self.a(produced_element_types=("map",))]).status,"FAIL")
 def test_compile_block(self):self.assertEqual(run_dsl_benchmark([self.a()],require_empirical_compile=True).status,"BLOCK")
 def test_render_block(self):self.assertEqual(run_dsl_benchmark([self.a()],require_empirical_render=True).status,"BLOCK")
 def test_not_accepted(self):self.assertFalse(run_dsl_benchmark([self.a()]).accepted)
