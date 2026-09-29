"""Additional negative contracts for the Section 16 legacy release migration."""
from dataclasses import replace
import unittest
from bie.qa.release_contracts import (
    GateEvidence, GateRequirement, ReleaseEvaluator, ReleasePolicy,
    enterprise_default_policy,
)


def evidence(gate, **changes):
    return replace(GateEvidence('ev-'+gate, gate, 'PASS', 'synthetic-check', '1',
        ['synthetic-artifact'], ['synthetic-evidence'], created_at='2000-01-01T00:00:00Z'), **changes)


class LegacyReleaseMigrationTests(unittest.TestCase):
    def setUp(self):
        self.policy = enterprise_default_policy()
        self.evidence = [evidence(g.gate_id) for g in self.policy.gates if g.mode=='REQUIRED']

    def assess(self, *extra, policy=None):
        result = ReleaseEvaluator.evaluate(policy or self.policy, self.evidence+list(extra))
        self.assertIs(result.release_authorized, False)
        self.assertIs(result.product_accepted, False)
        self.assertEqual(result.evaluation_scope, 'LEGACY_METADATA_ONLY')
        self.assertNotEqual(result.release_status, 'SUCCESS')
        return result

    def test_metadata_pass_is_contract_only(self):
        self.assertEqual(self.assess().release_status, 'CONTRACT_ONLY')

    def test_human_review_is_not_authorization(self):
        self.assertEqual(self.assess(policy=replace(self.policy, require_human_review=True)).release_status,
                         'READY_FOR_REVIEW')

    def test_required_pass_with_diagnostic_blocks(self):
        self.assertEqual(self.assess(evidence('source_grounding', diagnostics=['COUNTEREXAMPLE'])).release_status,
                         'BLOCKED')

    def test_optional_diagnostic_blocks(self):
        self.assertIn('performance', self.assess(evidence('performance', diagnostics=['OUT_OF_MEMORY'])).blocking_gates)

    def test_not_applicable_diagnostic_is_not_discarded(self):
        policy = replace(self.policy, gates=self.policy.gates+[
            GateRequirement('extra', 'NOT_APPLICABLE', 'QA')])
        result = self.assess(evidence('extra', diagnostics=['BLOCKER']), policy=policy)
        self.assertIn('extra', result.blocking_gates)
        self.assertEqual(next(g for g in result.gate_results if g.gate_id=='extra').diagnostics, ['BLOCKER'])

    def test_advisory_prefix_cannot_hide_string_diagnostic(self):
        self.assertEqual(self.assess(evidence('performance', diagnostics=['ADVISORY: unsafe'])).release_status,
                         'BLOCKED')

    def test_unknown_pass_gate_blocks(self):
        result = self.assess(evidence('invented'))
        self.assertIn('invented', result.blocking_gates)
        self.assertIn('UNKNOWN_EVIDENCE_GATE', result.gate_results[-1].diagnostics)

    def test_missing_required_evidence_stays_blocked(self):
        self.evidence = [e for e in self.evidence if e.gate_id!='game_runtime']
        self.assertIn('game_runtime', self.assess().blocking_gates)

    def test_required_fail_stays_blocked(self):
        result = self.assess(evidence('video_render', status='FAIL', summary='synthetic seeded failure'))
        self.assertIn('video_render', result.blocking_gates)

    def test_required_error_stays_blocked(self):
        result = self.assess(evidence('code_compile', status='ERROR', summary='synthetic compile error'))
        self.assertIn('code_compile', result.blocking_gates)

    def test_required_skip_stays_blocked(self):
        self.assertIn('game_build', self.assess(evidence('game_build', status='SKIPPED')).blocking_gates)

    def test_success_evidence_status_is_rejected(self):
        with self.assertRaises(ValueError):
            self.assess(evidence('video_render', status='SUCCESS'))

    def test_empty_metadata_does_not_authorize(self):
        self.evidence=[]
        self.assertEqual(self.assess().release_status, 'BLOCKED')

    def test_adding_blocker_never_improves_status(self):
        self.assertEqual(self.assess().release_status, 'CONTRACT_ONLY')
        self.assertEqual(self.assess(evidence('source_grounding', diagnostics=['BLOCKER'])).release_status,
                         'BLOCKED')

    def test_blocker_beats_human_review(self):
        self.assertEqual(self.assess(evidence('source_grounding', diagnostics=['BLOCKER']),
            policy=replace(self.policy, require_human_review=True)).release_status, 'BLOCKED')


if __name__ == '__main__':
    unittest.main()
