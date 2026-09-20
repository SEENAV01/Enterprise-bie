import unittest
from bie.scene_ir.dsl_section_gate import *
class T(unittest.TestCase):
 def e(self,**kw):
  d=dict(regression_passed=True,original_tasks_implemented=51,hardening_tasks_implemented=20,ani_adoption_passed=True,dsl_gate_passed=True,compiler_preflight_passed=True,actual_e2e_passed=True,realbook_harness_passed=True,benchmark_passed=True,mutation_gate_passed=True,empirical_compile_evidence=False,empirical_render_evidence=False,realbook_acceptance_evidence=False);d.update(kw);return DSLSectionEvidence(**d)
 def test_impl(self):self.assertEqual(evaluate_dsl_section_gate(self.e()).implementation_status,"IMPLEMENTATION_SCOPE_COMPLETE")
 def test_accept_block(self):self.assertEqual(evaluate_dsl_section_gate(self.e()).acceptance_status,"ACCEPTANCE_BLOCKED")
 def test_move(self):self.assertTrue(evaluate_dsl_section_gate(self.e()).can_move_to_comp)
 def test_hard_block(self):self.assertFalse(evaluate_dsl_section_gate(self.e(hardening_tasks_implemented=19)).can_move_to_comp)
 def test_accept(self):self.assertTrue(evaluate_dsl_section_gate(self.e(empirical_compile_evidence=True,empirical_render_evidence=True,realbook_acceptance_evidence=True)).accepted)
 def test_default_not(self):self.assertFalse(evaluate_dsl_section_gate(self.e()).accepted)
