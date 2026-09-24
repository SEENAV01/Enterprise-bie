import unittest
from dataclasses import replace
from bie.audio.common import AudioError
from bie.audio.acoustic_calibration import CalibrationDataset,CalibrationPolicy,calibrate
from tests.audio.h9_test_support import profile,dataset

class CalibrationTests(unittest.TestCase):
    def test_separated_dataset_calibrates(self):
        r=calibrate(dataset(profile())); self.assertEqual(r.status,'CALIBRATED'); self.assertEqual((r.false_positive_count,r.false_negative_count),(0,0))
    def test_test_fixture_can_calibrate_mechanics_but_scope_retained(self):
        ds=dataset(profile(),scope='TEST_FIXTURE_ONLY',held=False,independent=False); r=calibrate(ds); self.assertEqual(r.status,'CALIBRATED'); self.assertEqual(r.calibration_scope,'TEST_FIXTURE_ONLY')
    def test_independent_scope_requires_heldout(self):
        with self.assertRaisesRegex(AudioError,'CALIBRATION_SCOPE_CONTRADICTION'): dataset(profile(),scope='HELD_OUT_INDEPENDENT',held=False)
    def test_insufficient_correct_blocks(self):
        ds=dataset(profile()); ds=replace(ds,cases=tuple(c for c in ds.cases if c.label!='CORRECT')+ds.cases[:1]); r=calibrate(ds); self.assertIn('INSUFFICIENT_CORRECT_CASES',r.blockers)
    def test_insufficient_error_blocks(self):
        ds=dataset(profile()); ds=replace(ds,cases=tuple(c for c in ds.cases if c.label!='PRONUNCIATION_ERROR')+ds.cases[-1:]); r=calibrate(ds); self.assertIn('INSUFFICIENT_ERROR_CASES',r.blockers)
    def test_uncertainty_excluded(self):
        r=calibrate(dataset(profile(),uncertain=3)); self.assertEqual(r.excluded_uncertain_count,3)
    def test_too_many_uncertain_blocks(self):
        r=calibrate(dataset(profile(),uncertain=20)); self.assertIn('INSUFFICIENT_CORRECT_CASES',r.blockers)
    def test_no_threshold_blocks(self):
        ds=dataset(profile()); cases=tuple(replace(c,deviation_score_ppm=500_000) for c in ds.cases); r=calibrate(replace(ds,cases=cases)); self.assertIn('NO_THRESHOLD_MEETS_ERROR_BOUNDS',r.blockers)
    def test_policy_fingerprint_changes(self): self.assertNotEqual(CalibrationPolicy().fingerprint(),CalibrationPolicy(max_false_positive_ppm=1).fingerprint())
    def test_duplicate_case_rejected(self):
        ds=dataset(profile())
        with self.assertRaisesRegex(AudioError,'CALIBRATION_DUPLICATE_CASE'): replace(ds,cases=(ds.cases[0],ds.cases[0]))
    def test_profile_mix_rejected(self):
        ds=dataset(profile()); other=replace(ds.cases[0],evaluator_profile_fingerprint='sha256:'+'9'*64)
        with self.assertRaisesRegex(AudioError,'CALIBRATION_PROFILE_MIX'): replace(ds,cases=(other,*ds.cases[1:]))
    def test_language_label_coverage(self):
        ds=dataset(profile()); one=replace(ds.cases[0],language='hi-IN'); r=calibrate(replace(ds,cases=(one,*ds.cases[1:]))); self.assertIn('LANGUAGE_LABEL_COVERAGE:hi-IN',r.blockers)
    def test_language_coverage_can_be_relaxed_explicitly(self):
        ds=dataset(profile()); one=replace(ds.cases[0],language='hi-IN'); r=calibrate(replace(ds,cases=(one,*ds.cases[1:])),CalibrationPolicy(require_each_language_both_labels=False)); self.assertEqual(r.status,'CALIBRATED')
    def test_threshold_is_deterministic(self): self.assertEqual(calibrate(dataset(profile())).fingerprint(),calibrate(dataset(profile())).fingerprint())

if __name__=='__main__': unittest.main()
