from dataclasses import replace
import unittest
from bie.qa.release_v2 import ContractError, GateRule, ReleasePolicy, enterprise_policy
from helpers import CaseTest


class PolicyTests(CaseTest):
    def test_all_critical_gates_present(self):
        by_id = {rule.gate_id: rule for rule in self.policy.gates}
        for gid in ("mathematical_correctness", "reasoning_validity", "accessibility", "performance",
                    "game_runtime", "game_learning_alignment", "video_render", "rendered_frame_inspection",
                    "benchmark", "real_book_e2e", "canonical_integration"):
            self.assertIn(gid, by_id)
        self.assertEqual(len(by_id), 28)

    def test_no_mandatory_gate_can_be_deleted(self):
        for rule in self.policy.gates:
            with self.subTest(gate=rule.gate_id), self.assertRaisesRegex(ContractError, "WEAKENED_REQUIRED_GATE"):
                replace(self.policy, gates=tuple(g for g in self.policy.gates if g != rule))

    def test_runtime_cannot_accept_review_instead_of_execution(self):
        rules = tuple(replace(rule, allowed_kinds=("review",)) if rule.gate_id == "video_render" else rule
                      for rule in self.policy.gates)
        with self.assertRaisesRegex(ContractError, "WEAKENED_REQUIRED_GATE"):
            replace(self.policy, gates=rules)

    def test_required_role_cannot_be_dropped(self):
        rules = tuple(replace(rule, required_roles=("video",)) if rule.gate_id == "lineage_integrity" else rule
                      for rule in self.policy.gates)
        with self.assertRaises(ContractError):
            replace(self.policy, gates=rules)

    def test_zero_evidence_floor_rejected(self):
        with self.assertRaises(ContractError):
            replace(self.policy.gates[0], min_distinct_evaluators=0)

    def test_false_boolean_evidence_floor_rejected(self):
        with self.assertRaises(ContractError):
            replace(self.policy.gates[0], min_distinct_evaluators=True)

    def test_fixture_not_valid_policy_kind(self):
        with self.assertRaises(ContractError):
            replace(self.policy.gates[0], allowed_kinds=("fixture",))

    def test_duplicate_gate_rejected(self):
        with self.assertRaisesRegex(ContractError, "DUPLICATE_GATE_ID"):
            replace(self.policy, gates=self.policy.gates + (self.policy.gates[0],))

    def test_stronger_policy_allowed_and_digest_changes(self):
        rules = (replace(self.policy.gates[0], min_distinct_evaluators=2),) + self.policy.gates[1:]
        stronger = replace(self.policy, gates=rules)
        self.assertNotEqual(stronger.content_digest, self.policy.content_digest)

    def test_policy_order_has_no_semantic_effect(self):
        reordered = replace(self.policy, gates=tuple(reversed(self.policy.gates)))
        self.assertEqual(reordered.content_digest, self.policy.content_digest)

    def test_owner_routing_cannot_be_silently_changed(self):
        rules = (replace(self.policy.gates[0], owner="UNKNOWN"),) + self.policy.gates[1:]
        with self.assertRaisesRegex(ContractError, "OWNER_ROUTING_CHANGED"):
            replace(self.policy, gates=rules)

    def test_expiry_policy_cannot_be_unbounded(self):
        for value in (0, 604801, True, "100"):
            with self.subTest(value=value), self.assertRaises(ContractError):
                replace(self.policy, max_evidence_lifetime_seconds=value)


if __name__ == "__main__":
    unittest.main()
