from dataclasses import replace
from datetime import datetime, timedelta, timezone
import tempfile
import unittest
from pathlib import Path

from bie.director.authenticated_assessment import (SignedGradeSubmission, VerifiedGradeIdentity,
    AuthenticatedAssessmentPolicy, publish_authenticated_assessment, validate_authenticated_assessment)
from bie.director.teaching_context import publish_teaching_context, load_teaching_context
from context_fixtures import context_upstream


NOW = datetime(2026, 9, 14, 5, 0, tzinfo=timezone.utc)


class Verifier:
    def __init__(self, change=None): self.calls=[]; self.change=change
    def verify_grade(self, payload, signature, issuer, key_id, now):
        self.calls.append((payload, signature, issuer, key_id, now))
        identity = VerifiedGradeIdentity(issuer, key_id, 'fixture-learner', 'grade:1', NOW.isoformat(), 'AUTHENTICATED_GRADER')
        return replace(identity, **self.change) if self.change else identity


class AuthenticatedGradingTests(unittest.TestCase):
    def fixture(self):
        f = context_upstream(Path(tempfile.mkdtemp()), 'science')
        issued = (NOW - timedelta(minutes=1)).isoformat(); expires = (NOW + timedelta(minutes=10)).isoformat()
        submission = SignedGradeSubmission('grade:1', 'issuer:school', 'key:2026', 'fixture-learner',
            f.concepts[0].concept_id, 'assessment:charge', 'A grounded learner response', .8, .95,
            issued, expires, b'controlled-signature-bytes')
        return f, submission

    def publish(self, f, submission, verifier=None, policy=None):
        return publish_authenticated_assessment(f.io, f.run_id, f.source_ref, submission, verifier or Verifier(),
            now_utc=NOW.isoformat(), policy=policy or AuthenticatedAssessmentPolicy(allowed_issuers=('issuer:school',)))

    def test_verified_identity_binds_exact_grade_and_response(self):
        f, submission = self.fixture(); verifier=Verifier(); ref=self.publish(f,submission,verifier)
        event=f.io.load(ref); data=validate_authenticated_assessment(f.io,event,f.source_ref)
        self.assertEqual('AUTHENTICATED_GRADED_RESPONSE',data['score_origin'])
        self.assertEqual(1,len(verifier.calls));self.assertNotIn(submission.signature,verifier.calls[0][0])

    def test_context_consumes_authenticated_grade_without_calling_it_mastery_proof(self):
        f, submission=self.fixture(); grade=self.publish(f,submission)
        ref=publish_teaching_context(f.io,f.run_id,f.source_ref,f.concepts,f.prerequisites,f.derivations,(grade,))
        data=load_teaching_context(f.io,ref,f.source_ref).model_data()
        self.assertIn('STILL_UNCALIBRATED',data['mastery_interpretation'])
        self.assertIn('AUTHENTICATED_GRADE_STILL_REQUIRES_CALIBRATION_REVIEW',data['review_reasons'])

    def test_expired_or_future_grade_is_rejected_before_verifier_call(self):
        f, submission=self.fixture(); verifier=Verifier()
        expired=replace(submission,expires_at_utc=(NOW-timedelta(seconds=400)).isoformat())
        with self.assertRaises(ValueError): self.publish(f,expired,verifier)
        self.assertEqual([],verifier.calls)

    def test_wrong_issuer_is_rejected(self):
        f, submission=self.fixture()
        with self.assertRaises(ValueError): self.publish(f,replace(submission,issuer='issuer:other'))

    def test_identity_subject_grade_and_assurance_must_match(self):
        f, submission=self.fixture()
        for change in ({'subject':'other'},{'grade_id':'other'},{'assurance':'LOW'}):
            with self.subTest(change=change),self.assertRaises(ValueError): self.publish(f,submission,Verifier(change))

    def test_signature_is_binary_and_bounded(self):
        f, submission=self.fixture()
        for signature in (b'short',b'x'*8193,'not-bytes'):
            with self.subTest(signature=type(signature).__name__),self.assertRaises(ValueError):
                self.publish(f,replace(submission,signature=signature))

    def test_source_run_and_event_ancestry_are_enforced(self):
        f, submission=self.fixture(); ref=self.publish(f,submission); event=f.io.load(ref)
        event.payload['response_text']='edited after grading'
        with self.assertRaises(ValueError):validate_authenticated_assessment(f.io,event,f.source_ref)

    def test_every_signed_payload_field_is_rebound_during_read(self):
        f, submission=self.fixture(); ref=self.publish(f,submission)
        for field,value in (('score',.1),('item_id','other-item'),('issued_at_utc',(NOW-timedelta(minutes=2)).isoformat())):
            event=f.io.load(ref);event.payload[field]=value
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'signed payload'):
                validate_authenticated_assessment(f.io,event,f.source_ref)

    def test_reliability_and_score_are_bounded(self):
        f, submission=self.fixture()
        for change in ({'score':1.1},{'reliability':float('nan')}):
            with self.subTest(change=change),self.assertRaises(ValueError): self.publish(f,replace(submission,**change))


if __name__=='__main__':unittest.main()
