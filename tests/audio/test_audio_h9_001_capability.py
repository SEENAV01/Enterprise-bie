import unittest
from dataclasses import replace
from bie.audio.common import AudioError
from bie.audio.evaluator_capability import AccentBinding, EvaluatorProfile, EvaluationRequirements, negotiate
from tests.audio.h9_test_support import profile,requirements

class CapabilityTests(unittest.TestCase):
    def test_supported_profile(self): self.assertTrue(negotiate(profile(),requirements()).supported)
    def test_language_blocked(self): self.assertIn('UNSUPPORTED_LANGUAGE:fr-FR',negotiate(profile(),requirements(languages=('fr-FR',),accents=())).blockers)
    def test_accent_blocked(self): self.assertIn('UNSUPPORTED_ACCENT:en-US:scottish',negotiate(profile(),requirements(accents=(('en-US','scottish'),))).blockers)
    def test_ipa_blocked(self): self.assertIn('IPA_TARGETS_UNSUPPORTED',negotiate(profile(ipa=False),requirements()).blockers)
    def test_oov_blocked(self): self.assertIn('OOV_TARGETS_UNSUPPORTED',negotiate(profile(oov=False),requirements()).blockers)
    def test_code_switch_blocked(self): self.assertIn('CODE_SWITCHING_UNSUPPORTED',negotiate(profile(code=False),requirements(code=True)).blockers)
    def test_target_budget(self): self.assertIn('TARGET_BUDGET_EXCEEDED',negotiate(replace(profile(),max_targets=1),requirements()).blockers)
    def test_audio_budget(self): self.assertIn('AUDIO_BUDGET_EXCEEDED',negotiate(replace(profile(),max_audio_seconds=1),requirements()).blockers)
    def test_required_outputs(self):
        with self.assertRaisesRegex(AudioError,'EVALUATOR_OUTPUTS'): replace(profile(),outputs=('word_boundaries',))
    def test_duplicate_language(self):
        with self.assertRaisesRegex(AudioError,'EVALUATOR_LANGUAGE_DUPLICATE'): replace(profile(),supported_languages=('en-US','en-US'))
    def test_accent_language_must_exist(self):
        with self.assertRaisesRegex(AudioError,'EVALUATOR_ACCENT_LANGUAGE'): replace(profile(),accent_bindings=(AccentBinding('fr-FR','general',('x',)),))
    def test_decision_is_not_accuracy_claim(self): self.assertEqual(negotiate(profile(),requirements()).scope,'CAPABILITY_NEGOTIATION_NOT_ACCURACY')
    def test_requirements_fingerprint_changes(self): self.assertNotEqual(requirements().fingerprint(),requirements(ipa=False).fingerprint())

if __name__=='__main__': unittest.main()
