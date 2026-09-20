import unittest
from bie.animation_intelligence.ani_computed_benchmark import *
def A(**kw):
 d=dict(case_id="c",required_track_ids=("t",),produced_track_ids=("t",),qa_blockers=(),trace_blockers=(),
 sceneir_blockers=(),sync_error_ms=0,motion_budget_ratio=.8,empirical_render_status="NOT_RUN");d.update(kw);return BenchmarkArtifact(**d)
class T(unittest.TestCase):
 def test_case(self):self.assertEqual(compute_case_metrics(A()).aggregate,1.0)
 def test_pass(self):self.assertEqual(run_computed_benchmark([A()]).status,"PASS")
 def test_coverage(self):self.assertEqual(run_computed_benchmark([A(produced_track_ids=())]).status,"BLOCKED")
 def test_trace(self):self.assertEqual(run_computed_benchmark([A(trace_blockers=("x",))]).status,"BLOCKED")
 def test_sceneir(self):self.assertEqual(run_computed_benchmark([A(sceneir_blockers=("x",))]).status,"BLOCKED")
 def test_sync(self):self.assertEqual(run_computed_benchmark([A(sync_error_ms=900)]).status,"BLOCKED")
 def test_empirical(self):self.assertEqual(run_computed_benchmark([A()],require_empirical_render=True).status,"BLOCKED")
 def test_not_accepted(self):self.assertFalse(run_computed_benchmark([A()]).accepted)
