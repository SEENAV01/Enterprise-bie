"""Synthetic positive and seeded-negative Section 16 oracle-depth controls.

These cases do not claim native browser execution or real learner transfer.
"""
from dataclasses import replace
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests' / 'qa_game16'))
from game_helpers import FixtureCase, Action, LearningTarget, Scenario, State, Transition, Value
from bie.qa.release_v2.contracts import ContractError
from bie.section16.oracle_depth import DepthRequirement, assess_oracle_depth


class OracleDepthTests(FixtureCase):
    def depth_policy(self):
        p = self.p
        final = State('transfer-win', tuple(
            replace(v, text='transfer-complete') if v.key == 'status' else v
            for v in next(s for s in p.states if s.state_id == 'win').values
        ), True, True)
        transfer = LearningTarget(
            'apply-equation', 'transfer-balance', 'apply-new-context',
            'transfer-prompt', 'prompt', 'transfer-correct', 'transfer-incorrect', 'feedback',
            ('transfer',), 'transfer-win', 'wrong',
        )
        return replace(
            p,
            states=p.states + (final,),
            actions=p.actions + (Action('transfer', 'click', '#transfer', ''),),
            transitions=p.transitions + (Transition('edge-transfer', 'win', 'transfer', 'transfer-win'),),
            scenarios=p.scenarios + (
                Scenario('remediate', 480, 320, ('submit', 'reset', 'increase', 'increase', 'submit')),
                Scenario('transfer-route', 480, 320, ('increase', 'increase', 'submit', 'transfer')),
            ),
            learning=p.learning + (transfer,),
        )

    def requirements(self):
        return (
            DepthRequirement('branch', ('pointer',), ('balance',)),
            DepthRequirement('remediation', ('remediate',), ('balance',)),
            DepthRequirement('transfer', ('transfer-route',), ('balance', 'transfer-balance')),
            DepthRequirement('reset', ('keyboard',), ()),
        )

    def test_positive_structural_routes_remain_not_observed(self):
        result = assess_oracle_depth(self.depth_policy(), self.requirements())
        self.assertEqual(result.structural_status, 'CHECKS_PASSED')
        self.assertEqual(result.observation_status, 'NOT_RUN')
        self.assertIn('edge-transfer', result.required_transition_ids)
        self.assertFalse(result.to_safe_dict()['native_game_acceptance'])
        self.assertFalse(result.to_safe_dict()['learner_mastery_proven'])

    def test_repeat_is_deterministic(self):
        p = self.depth_policy()
        self.assertEqual(assess_oracle_depth(p, self.requirements()).to_safe_dict(),
                         assess_oracle_depth(p, self.requirements()).to_safe_dict())

    def test_branch_requires_success_and_error(self):
        req = list(self.requirements())
        req[0] = DepthRequirement('branch', ('keyboard',), ('balance',))
        self.assertIn('GAME_DEPTH_BRANCH_MISSING', assess_oracle_depth(self.depth_policy(), tuple(req)).findings)

    def test_remediation_requires_error_then_success(self):
        req = list(self.requirements())
        req[1] = DepthRequirement('remediation', ('pointer',), ('balance',))
        self.assertIn('GAME_DEPTH_REMEDIATION_MISSING', assess_oracle_depth(self.depth_policy(), tuple(req)).findings)

    def test_transfer_requires_separate_declared_objective_and_prompt(self):
        p = self.depth_policy()
        p = replace(p, learning=p.learning[:1] + (replace(p.learning[1], objective_id='solve-equation'),))
        self.assertIn('GAME_DEPTH_TRANSFER_NOT_DISTINCT', assess_oracle_depth(p, self.requirements()).findings)

    def test_transfer_requires_second_success_route(self):
        req = list(self.requirements())
        req[2] = DepthRequirement('transfer', ('pointer',), ('balance', 'transfer-balance'))
        self.assertIn('GAME_DEPTH_TRANSFER_MISSING', assess_oracle_depth(self.depth_policy(), tuple(req)).findings)

    def test_transfer_cannot_reuse_original_feedback_claims(self):
        p = self.depth_policy()
        p = replace(p, learning=p.learning[:1] + (replace(p.learning[1], correct_claim_id='correct'),))
        self.assertIn('GAME_DEPTH_TRANSFER_NOT_DISTINCT', assess_oracle_depth(p, self.requirements()).findings)

    def test_reset_must_follow_terminal_state(self):
        req = list(self.requirements())
        req[3] = DepthRequirement('reset', ('remediate',), ())
        self.assertIn('GAME_DEPTH_RESET_MISSING', assess_oracle_depth(self.depth_policy(), tuple(req)).findings)

    def test_unknown_scenario_is_not_arbitrarily_substituted(self):
        req = list(self.requirements())
        req[0] = DepthRequirement('branch', ('not-a-scenario',), ('balance',))
        self.assertIn('GAME_DEPTH_UNKNOWN_SCENARIO', assess_oracle_depth(self.depth_policy(), tuple(req)).findings)

    def test_unknown_challenge_is_not_arbitrarily_substituted(self):
        req = list(self.requirements())
        req[0] = DepthRequirement('branch', ('pointer',), ('unknown',))
        self.assertIn('GAME_DEPTH_UNKNOWN_CHALLENGE', assess_oracle_depth(self.depth_policy(), tuple(req)).findings)

    def test_role_omission_rejected(self):
        self.assertRaises(ContractError, assess_oracle_depth, self.depth_policy(), self.requirements()[:-1])

    def test_duplicate_role_rejected(self):
        req = list(self.requirements())
        req[3] = DepthRequirement('branch', ('pointer',), ('balance',))
        self.assertRaises(ContractError, assess_oracle_depth, self.depth_policy(), tuple(req))

    def test_result_from_other_policy_rejected(self):
        self.assertRaises(ContractError, assess_oracle_depth, self.depth_policy(), self.requirements(), game_result=self.check())

    def test_requirement_schema_rejects_wrong_challenge_count(self):
        self.assertRaises(ContractError, DepthRequirement, 'transfer', ('transfer-route',), ('balance',))

    def test_requirement_schema_rejects_unhashable_identifier_without_type_leak(self):
        self.assertRaises(ContractError, DepthRequirement, 'branch', ({'bad': 'id'},), ('balance',))
