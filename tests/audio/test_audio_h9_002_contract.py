import unittest
from dataclasses import replace
from bie.audio.common import AudioError
from bie.audio.evaluator_contract import EvaluationTarget, EvaluatedTarget, EvaluationReport, request_from_targets, validate_report
from tests.audio.h9_test_support import *

class ContractTests(unittest.TestCase):
    def test_request_builds(self): self.assertEqual(len(request().targets),2)
    def test_blocked_capability_rejects_request(self):
        with self.assertRaisesRegex(AudioError,'EVALUATOR_CAPABILITY_BLOCKED'): request(prof=profile(ipa=False))
    def test_target_count_binding(self):
        with self.assertRaisesRegex(AudioError,'EVALUATOR_REQUIREMENT_TARGET_COUNT'): request(req=requirements(count=1))
    def test_report_validates(self): self.assertEqual(validate_report(report(),request(),profile()).report_scope,'MEASUREMENT_NOT_ACCEPTANCE')
    def test_request_binding_tamper(self):
        r=request(); p=profile(); rep=report(r,p)
        with self.assertRaisesRegex(AudioError,'EVALUATOR_REPORT_BINDING'): validate_report(replace(rep,request_fingerprint='sha256:'+'8'*64),r,p)
    def test_media_tamper(self):
        r=request(); p=profile(); rep=report(r,p)
        with self.assertRaisesRegex(AudioError,'EVALUATOR_REPORT_MEDIA_CHANGED'): validate_report(replace(rep,media_sha256='9'*64),r,p)
    def test_identity_tamper(self):
        r=request(); p=profile(); rep=report(r,p)
        with self.assertRaisesRegex(AudioError,'EVALUATOR_REPORT_IDENTITY'): validate_report(replace(rep,model_revision='r2'),r,p)
    def test_coverage_missing(self):
        r=request(); p=profile(); rep=report(r,p)
        with self.assertRaisesRegex(AudioError,'EVALUATOR_REPORT_COVERAGE'): validate_report(replace(rep,targets=(rep.targets[0],)),r,p)
    def test_duplicate_target_rejected(self):
        rep=report()
        with self.assertRaisesRegex(AudioError,'EVALUATOR_REPORT_DUPLICATE_TARGET'): replace(rep,targets=(rep.targets[0],rep.targets[0]))
    def test_oov_must_be_handled(self):
        r=request(); p=profile(); rep=report(r,p); bad=replace(rep.targets[0],oov_handled=False)
        with self.assertRaisesRegex(AudioError,'EVALUATOR_REPORT_OOV_UNHANDLED'): validate_report(replace(rep,targets=(bad,rep.targets[1])),r,p)
    def test_ipa_needs_phone_evidence(self):
        r=request(); p=profile(); rep=report(r,p); bad=replace(rep.targets[0],observed_phones=())
        with self.assertRaisesRegex(AudioError,'EVALUATOR_REPORT_IPA_EVIDENCE_MISSING'): validate_report(replace(rep,targets=(bad,rep.targets[1])),r,p)
    def test_unmeasured_cannot_carry_score(self):
        with self.assertRaisesRegex(AudioError,'EVALUATOR_UNMEASURED_SCORE'): EvaluatedTarget(TARGET1,'UNSUPPORTED',1,1,(),None,None,False,())
    def test_measured_needs_score_and_bounds(self):
        with self.assertRaisesRegex(AudioError,'EVALUATOR_MEASURED_INCOMPLETE'): EvaluatedTarget(TARGET1,'MEASURED',None,None,(),None,None,False,())
    def test_report_outside_media_rejected(self):
        r=request(); p=profile(); rep=report(r,p); bad=replace(rep.targets[0],word_end_sample=r.total_samples+1)
        with self.assertRaisesRegex(AudioError,'EVALUATOR_REPORT_WORD_OUT_OF_MEDIA'): validate_report(replace(rep,targets=(bad,rep.targets[1])),r,p)

if __name__=='__main__': unittest.main()
