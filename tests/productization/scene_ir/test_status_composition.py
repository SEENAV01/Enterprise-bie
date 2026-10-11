"""Status composition controls, not substitutes for native process evidence."""
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch
import unittest

from bie.productization.scene_ir_slice import SceneIRProducerService, STAGES
from bie.productization.animation_slice import AnimationProducerService
from bie.productization.director_slice import DirectorProducerService

VISUAL = ('output_artifact_id', 'output_sha256', 'schema_version', 'plan_fingerprint',
    'visual_intent_count', 'abstention_count', 'internal_stage_count', 'validation',
    'animation_input_compatibility', 'requires_review', 'accepted', 'release_ready')
ANIMATION = ('output_artifact_id', 'output_sha256', 'schema_version', 'plan_fingerprint',
    'track_count', 'internal_stage_count', 'validation', 'sceneir_handoff_ready',
    'requires_review', 'accepted', 'release_ready', 'audio_complete', 'audio_reconciliation_open')
SCENE = ('output_artifact_id', 'output_sha256', 'schema_version', 'document_fingerprint',
    'element_count', 'track_count', 'native_validator_count', 'single_scene', 'validation',
    'compiler_loader_admitted', 'requires_review', 'accepted', 'release_ready',
    'audio_complete', 'audio_reconciliation_open')


class StatusCompositionControls(unittest.TestCase):
    def setUp(self):
        self.service = object.__new__(SceneIRProducerService)
        self.states = dict.fromkeys(STAGES, 'SUCCEEDED')
        self.service.persistence = SimpleNamespace(load_run_state=lambda run: dict(stages={
            k: dict(attempts=[dict(state=v)]) for k, v in self.states.items()}))
        self.base = dict(stages=deepcopy(self.states), director={'validation': 'PASS'}, product_accepted=False)
        self.visual = dict.fromkeys(VISUAL, 'verified-visual')
        self.animation = dict.fromkeys(ANIMATION, 'verified-animation')
        self.scene = dict.fromkeys(SCENE, 'verified-scene')
        for receipt in (self.visual, self.animation, self.scene):
            receipt.update(requires_review=True, accepted=False, release_ready=False,
                           audio_complete=False, audio_reconciliation_open=True)
            receipt['private_payload'] = 'private synthetic marker MUST NOT appear'
        self.bundle = ({}, self.scene, dict(visual_receipt=self.visual), self.animation)

    def status(self):
        with patch.object(DirectorProducerService, 'status', return_value=deepcopy(self.base)) as lower, \
             patch.object(AnimationProducerService, 'status', side_effect=AssertionError('DUPLICATE_CHAIN')) as duplicate, \
             patch.object(self.service, '_verified_scene_bundle', return_value=self.bundle) as verified:
            result = self.service.status('run', 'tenant')
            lower.assert_called_once_with(self.service, 'run', 'tenant')
            duplicate.assert_not_called()
            verified.assert_called_once_with('run', 'tenant')
        return result

    def test_completed_status_uses_one_fresh_full_bundle(self):
        result = self.status()
        self.assertEqual(result['director'], self.base['director'])
        self.assertEqual(result['stages'], self.states)

    def test_safe_projections_retain_exact_historical_field_sets(self):
        result = self.status()
        self.assertEqual(result['visual'], {k: self.visual[k] for k in VISUAL})
        self.assertEqual(result['animation'], {k: self.animation[k] for k in ANIMATION})
        self.assertEqual(result['scene_ir'], {k: self.scene[k] for k in SCENE})
        self.assertNotIn('private_payload', result['visual'])
        self.assertNotIn('private_payload', result['animation'])
        self.assertNotIn('private_payload', result['scene_ir'])

    def test_incomplete_status_preserves_inherited_path(self):
        self.states['SCENE_IR'] = 'READY'
        legacy = dict(stages=deepcopy(self.states), visual={'existing': 1}, animation={'existing': 2})
        with patch.object(AnimationProducerService, 'status', return_value=legacy) as inherited, \
             patch.object(DirectorProducerService, 'status', side_effect=AssertionError('WRONG_PATH')), \
             patch.object(self.service, '_verified_scene_bundle', side_effect=AssertionError('PREMATURE')):
            result = self.service.status('run', 'tenant')
            inherited.assert_called_once_with('run', 'tenant')
            self.assertIs(result, legacy)
            self.assertIsNone(result['scene_ir'])

    def test_fresh_verification_rejection_propagates_unchanged(self):
        rejection = RuntimeError('synthetic guard rejection')
        with patch.object(DirectorProducerService, 'status', return_value=self.base), \
             patch.object(self.service, '_verified_scene_bundle', side_effect=rejection):
            with self.assertRaises(RuntimeError) as caught:
                self.service.status('run', 'tenant')
            self.assertIs(caught.exception, rejection)

    def test_lower_stage_authority_rejection_is_not_bypassed(self):
        rejection = RuntimeError('synthetic ancestor rejection')
        with patch.object(DirectorProducerService, 'status', side_effect=rejection), \
             patch.object(self.service, '_verified_scene_bundle') as verified:
            with self.assertRaises(RuntimeError) as caught:
                self.service.status('run', 'tenant')
            self.assertIs(caught.exception, rejection)
            verified.assert_not_called()

    def test_each_read_revalidates_without_cross_call_cache(self):
        with patch.object(DirectorProducerService, 'status', side_effect=lambda *args: deepcopy(self.base)), \
             patch.object(self.service, '_verified_scene_bundle', return_value=self.bundle) as verified:
            first = self.service.status('run', 'tenant')
            self.visual['output_sha256'] = 'changed-and-reverified'
            second = self.service.status('run', 'tenant')
            self.assertEqual(verified.call_count, 2)
            self.assertNotEqual(first['visual']['output_sha256'], second['visual']['output_sha256'])

    def test_public_verified_scene_api_keeps_two_tuple(self):
        with patch.object(self.service, '_verified_scene_bundle', return_value=self.bundle) as verified:
            value = self.service.verified_scene_ir('run', 'tenant')
            self.assertEqual(value, self.bundle[:2])
            verified.assert_called_once_with('run', 'tenant')

    def test_missing_verified_upstream_field_fails_closed(self):
        del self.visual['output_sha256']
        with self.assertRaises(KeyError):
            self.status()


if __name__ == '__main__':
    unittest.main()
