import unittest
from bie.animation_intelligence.ani_section_gate import *
def E(**kw):
 d=dict(regression_passed=True,original_tasks_implemented=38,hardening_tasks_implemented=20,
 sceneir_handoff_passed=True,actual_e2e_passed=True,realbook_harness_passed=True,
 benchmark_passed=True,mutation_gate_passed=True,empirical_render_evidence=False,
 realbook_acceptance_evidence=False);d.update(kw);return AniSectionEvidence(**d)
class T(unittest.TestCase):
 def test_impl_complete(self):self.assertEqual(evaluate_ani_section_gate(E()).implementation_status,"IMPLEMENTATION_SCOPE_COMPLETE")
 def test_move(self):self.assertTrue(evaluate_ani_section_gate(E()).can_move_to_scene_ir)
 def test_accept_blocked(self):self.assertEqual(evaluate_ani_section_gate(E()).acceptance_status,"ACCEPTANCE_BLOCKED")
 def test_render_blocker(self):self.assertIn("empirical_render_evidence_missing",evaluate_ani_section_gate(E()).acceptance_blockers)
 def test_hardening_gap(self):self.assertEqual(evaluate_ani_section_gate(E(hardening_tasks_implemented=19)).implementation_status,"IMPLEMENTED_WITH_GAPS")
 def test_e2e_gap(self):self.assertFalse(evaluate_ani_section_gate(E(actual_e2e_passed=False)).can_move_to_scene_ir)
 def test_accepted(self):self.assertTrue(evaluate_ani_section_gate(E(empirical_render_evidence=True,realbook_acceptance_evidence=True)).accepted)
 def test_not_self_accept(self):self.assertFalse(evaluate_ani_section_gate(E()).accepted)
