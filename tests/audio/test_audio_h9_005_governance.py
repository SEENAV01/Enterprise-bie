import unittest
from dataclasses import replace
from bie.audio.common import AudioError
from bie.audio.pronunciation_governance import decide,repair_intents
from tests.audio.h9_test_support import *

class GovernanceTests(unittest.TestCase):
    def test_all_good_passes_under_production_authority(self):
        p=profile(); r=request(p); rep=report(r,p); c=calibration(p); s,t=authority(p,c); d=decide(r,rep,p,c,s,t,now=NOW); self.assertEqual(d.overall,'PASS'); self.assertTrue(d.pronunciation_verified)
    def test_mismatch_fails(self):
        p=profile(); r=request(p); rep=report(r,p,scores=(900_000,100_000)); c=calibration(p); s,t=authority(p,c); d=decide(r,rep,p,c,s,t,now=NOW); self.assertEqual(d.overall,'FAIL')
    def test_high_uncertainty_reviews(self):
        p=profile(); r=request(p); rep=report(r,p,uncertainties=(900_000,50_000)); c=calibration(p); s,t=authority(p,c); d=decide(r,rep,p,c,s,t,now=NOW); self.assertEqual(d.overall,'REVIEW')
    def test_unmeasured_blocks(self):
        p=profile(); r=request(p); rep=report(r,p,statuses=('UNSUPPORTED','MEASURED')); c=calibration(p); s,t=authority(p,c); d=decide(r,rep,p,c,s,t,now=NOW); self.assertEqual(d.overall,'BLOCKED')
    def test_test_authority_blocks(self):
        p=profile(); r=request(p); rep=report(r,p); c=calibration(p); s,t=authority(p,c,production=False,custody='EPHEMERAL_TEST'); d=decide(r,rep,p,c,s,t,now=NOW); self.assertEqual(d.overall,'BLOCKED')
    def test_test_fixture_calibration_blocks(self):
        p=profile(); r=request(p); rep=report(r,p); c=calibrate(dataset(p,scope='TEST_FIXTURE_ONLY',held=False,independent=False)); s,t=authority(p,c); d=decide(r,rep,p,c,s,t,now=NOW); self.assertEqual(d.overall,'BLOCKED')
    def test_product_never_accepted(self):
        p=profile(); r=request(p); rep=report(r,p); c=calibration(p); s,t=authority(p,c); self.assertFalse(decide(r,rep,p,c,s,t,now=NOW).product_accepted)
    def test_fail_creates_repair_intent(self):
        p=profile(); r=request(p); rep=report(r,p,scores=(900_000,100_000)); c=calibration(p); s,t=authority(p,c); d=decide(r,rep,p,c,s,t,now=NOW); intents=repair_intents(d,r); self.assertEqual(len(intents),1); self.assertFalse(intents[0]['dispatch_performed'])
    def test_repair_preserves_reading(self):
        p=profile(); r=request(p); rep=report(r,p,scores=(900_000,100_000)); c=calibration(p); s,t=authority(p,c); i=repair_intents(decide(r,rep,p,c,s,t,now=NOW),r)[0]; self.assertEqual(i['expected_spoken'],r.targets[0].expected_spoken); self.assertEqual(i['expected_ipa'],r.targets[0].expected_ipa)
    def test_repair_declares_downstream_invalidation(self):
        p=profile(); r=request(p); rep=report(r,p,scores=(900_000,100_000)); c=calibration(p); s,t=authority(p,c); i=repair_intents(decide(r,rep,p,c,s,t,now=NOW),r)[0]; self.assertIn('RENDER',i['invalidates']); self.assertIn('ANIMATION_CLOCKS',i['invalidates'])
    def test_no_repair_for_pass(self):
        p=profile(); r=request(p); rep=report(r,p); c=calibration(p); s,t=authority(p,c); self.assertEqual(repair_intents(decide(r,rep,p,c,s,t,now=NOW),r),())
    def test_stale_report_rejected(self):
        p=profile(); r=request(p); rep=replace(report(r,p),request_fingerprint='sha256:'+'8'*64); c=calibration(p); s,t=authority(p,c)
        with self.assertRaisesRegex(AudioError,'EVALUATOR_REPORT_BINDING'): decide(r,rep,p,c,s,t,now=NOW)
    def test_calibration_profile_mismatch_rejected(self):
        p=profile(); r=request(p); rep=report(r,p); c=replace(calibration(p),evaluator_profile_fingerprint='sha256:'+'8'*64); s,t=authority(p,c)
        with self.assertRaisesRegex(AudioError,'PRONUNCIATION_CALIBRATION_BINDING|EVALUATOR_AUTHORITY'): decide(r,rep,p,c,s,t,now=NOW)
    def test_repair_request_binding_required(self):
        p=profile(); r=request(p); rep=report(r,p,scores=(900_000,100_000)); c=calibration(p); s,t=authority(p,c); d=decide(r,rep,p,c,s,t,now=NOW); r2=replace(r,clock_fingerprint='sha256:'+'9'*64)
        with self.assertRaisesRegex(AudioError,'PRONUNCIATION_REPAIR_INPUT'): repair_intents(d,r2)

if __name__=='__main__': unittest.main()
