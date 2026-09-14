from dataclasses import replace
from datetime import datetime, timezone
import unittest

from bie.director.provider_calibration import (CalibrationPolicy, ProviderStackIdentity,
    SignedBenchmarkRelease, VerifiedBenchmarkIdentity, planned_calibration,
    run_provider_calibration, source_receipts)
from bie.director.source_grounding_qa import SourceBytes
from examples.director_benchmark import candidate_identity, controlled_director, load_suite
from annotation_fixtures import ANNOTATOR
from annotation_review_fixtures import REVIEWER
from directing_fixtures import GENERATOR
from semantic_fixtures import IDENTITY


NOW=datetime(2026,9,14,6,0,tzinfo=timezone.utc).isoformat()


class AuthorityVerifier:
    def __init__(self,change=None,reject=False):self.calls=[];self.change=change or {};self.reject=reject
    def verify_benchmark(self,payload,signature,authority,key_id,now):
        self.calls.append((payload,signature,authority,key_id,now))
        if self.reject:raise ValueError('controlled invalid signature')
        base=VerifiedBenchmarkIdentity(authority,key_id,'release:1',NOW,'INDEPENDENT_BENCHMARK_AUTHORITY')
        return replace(base,**self.change)


class ProviderCalibrationTests(unittest.TestCase):
    def setUp(self):
        self.suite,self.sources=load_suite();identity=candidate_identity()
        self.stack=ProviderStackIdentity(GENERATOR,IDENTITY,ANNOTATOR,REVIEWER,identity,
            'CONTROLLED_PROTOCOL','controlled-test-environment')

    def release(self,**changes):
        base=SignedBenchmarkRelease('release:1','authority:independent','key:2026',self.suite.fingerprint(),
            self.suite.oracle_author,self.suite.oracle_method,source_receipts(self.suite,self.sources),NOW,
            b'controlled-benchmark-signature')
        return replace(base,**changes)

    def test_missing_external_candidate_is_truthfully_not_run(self):
        report=planned_calibration('calibration:planned',self.suite,self.sources,self.stack,
            'No external provider credentials or independent release were supplied.')
        self.assertEqual(report.status,'NOT_RUN');self.assertIsNone(report.benchmark_report)
        self.assertFalse(report.eligible_for_acceptance_review);self.assertFalse(report.accepted)

    def test_signed_controlled_run_executes_but_is_not_live_or_accepted(self):
        verifier=AuthorityVerifier();report=run_provider_calibration('calibration:controlled',self.suite,self.sources,
            self.stack,controlled_director,self.release(),verifier,now_utc=NOW)
        self.assertEqual(report.status,'EXECUTED');self.assertTrue(report.benchmark_report.checks_passed)
        self.assertFalse(dict(report.gates)['EXTERNAL_PROVIDER_EXECUTED'])
        self.assertFalse(report.eligible_for_acceptance_review);self.assertFalse(report.accepted)
        self.assertEqual(len(verifier.calls),1);self.assertNotIn(self.release().signature,verifier.calls[0][0])

    def test_release_binds_exact_suite_oracle_and_source_bytes(self):
        for change in ({'suite_fingerprint':'sha256:'+'0'*64},{'oracle_method':'changed'},
                       {'source_byte_receipts':()}):
            with self.subTest(change=change),self.assertRaisesRegex(ValueError,'exact suite'):
                run_provider_calibration('calibration:x',self.suite,self.sources,self.stack,
                    controlled_director,self.release(**change),AuthorityVerifier(),now_utc=NOW)

    def test_source_tampering_fails_before_oracle_or_candidate_execution(self):
        verifier=AuthorityVerifier();calls=[]
        sources=(replace(self.sources[0],data=b'changed'),)+self.sources[1:]
        with self.assertRaises(ValueError):run_provider_calibration('calibration:x',self.suite,sources,self.stack,
            lambda request:calls.append(request),self.release(),verifier,now_utc=NOW)
        self.assertEqual((verifier.calls,calls),([],[]))

    def test_verifier_identity_and_assurance_are_exact(self):
        for change in ({'release_id':'other'},{'key_id':'other'},{'assurance':'LOW'}):
            with self.subTest(change=change),self.assertRaises(ValueError):
                run_provider_calibration('calibration:x',self.suite,self.sources,self.stack,
                    controlled_director,self.release(),AuthorityVerifier(change),now_utc=NOW)

    def test_signature_is_bounded_and_authority_verifier_can_reject(self):
        for signature in (b'short',b'x'*8193):
            with self.subTest(size=len(signature)),self.assertRaises(ValueError):
                run_provider_calibration('calibration:x',self.suite,self.sources,self.stack,
                    controlled_director,self.release(signature=signature),AuthorityVerifier(),now_utc=NOW)
        with self.assertRaises(ValueError):run_provider_calibration('calibration:x',self.suite,self.sources,self.stack,
            controlled_director,self.release(),AuthorityVerifier(reject=True),now_utc=NOW)

    def test_annotation_and_reviewer_identity_must_be_independent(self):
        stack=replace(self.stack,reviewer=ANNOTATOR)
        with self.assertRaisesRegex(ValueError,'independent'):planned_calibration('calibration:x',self.suite,self.sources,stack,'not run')

    def test_failed_candidate_remains_executed_evidence_not_acceptance(self):
        report=run_provider_calibration('calibration:failed',self.suite,self.sources,self.stack,
            lambda _: {'passed':True},self.release(),AuthorityVerifier(),now_utc=NOW)
        self.assertEqual(report.status,'EXECUTED');self.assertFalse(report.benchmark_report.checks_passed)
        self.assertFalse(report.eligible_for_acceptance_review);self.assertFalse(report.accepted)

    def test_policy_and_provider_configuration_change_report_identity(self):
        first=planned_calibration('calibration:x',self.suite,self.sources,self.stack,'not run')
        stack=replace(self.stack,deployment_environment='another-controlled-environment')
        second=planned_calibration('calibration:x',self.suite,self.sources,stack,'not run')
        third=planned_calibration('calibration:x',self.suite,self.sources,self.stack,'not run',
            CalibrationPolicy(minimum_case_fraction=.9))
        self.assertNotEqual(first.fingerprint(),second.fingerprint());self.assertNotEqual(first.fingerprint(),third.fingerprint())


if __name__=='__main__':unittest.main()
