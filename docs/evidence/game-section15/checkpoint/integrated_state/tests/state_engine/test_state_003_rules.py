import unittest
from dataclasses import replace
from bie.game_engine.errors import GameContractError
from bie.game_engine.expressions import *
from bie.game_engine.interaction import RuleSpec,EffectSpec,EffectKind,InteractionContract
from bie.game_engine.state_engine.fixtures import *
from bie.game_engine.state_engine.rules import *
from tests.state_engine.support import snapshot_values

class RuleProgramTests(unittest.TestCase):
 def setUp(self):self.level=sample_level()
 def test_compile_rule_program(self):
  p=compile_rules(self.level);self.assertEqual(p.execution_order,('rule:move',));self.assertTrue(p.program_fingerprint.startswith('sha256:'))
 def test_eligible_initial_rule(self):self.assertEqual(eligible_rules(self.level,sample_snapshot()),('rule:move',))
 def test_rule_not_eligible_after_target(self):self.assertEqual(eligible_rules(self.level,snapshot_values(x=2.0)),())
 def test_stable_priority_order(self):
  r1=self.level.interaction.rules[0];r2=replace(r1,rule_id='rule:other',priority=5,effects=(EffectSpec('attempts',EffectKind.ADD,1),))
  lvl=replace(self.level,interaction=replace(self.level.interaction,rules=(r2,r1)));self.assertEqual(compile_rules(lvl).execution_order,('rule:move','rule:other'))
 def test_conflicting_priority_tie_fails(self):
  r1=self.level.interaction.rules[0];r2=replace(r1,rule_id='rule:other')
  lvl=replace(self.level,interaction=replace(self.level.interaction,rules=(r1,r2)))
  with self.assertRaisesRegex(GameContractError,'GAME_STATE_RULE_PRIORITY_CONFLICT'):compile_rules(lvl)
 def test_disjoint_priority_tie_allowed(self):
  r1=self.level.interaction.rules[0];r2=replace(r1,rule_id='rule:other',effects=(EffectSpec('attempts',EffectKind.ADD,1),))
  lvl=replace(self.level,interaction=replace(self.level.interaction,rules=(r1,r2)));self.assertEqual(len(compile_rules(lvl).rules),2)
 def test_unknown_variable_rejected_by_level_contract(self):
  r=replace(self.level.interaction.rules[0],condition=Compare(CompareOp.EQ,Variable('missing'),Literal(1)))
  with self.assertRaises(GameContractError):replace(self.level,interaction=replace(self.level.interaction,rules=(r,))).validate()
 def test_grounding_preserved(self):self.assertEqual(compile_rules(self.level).rules[0].grounding_refs,('source:book',))
 def test_program_deterministic(self):self.assertEqual(compile_rules(self.level),compile_rules(self.level))
 def test_product_acceptance_false(self):self.assertFalse(compile_rules(self.level).product_accepted)
