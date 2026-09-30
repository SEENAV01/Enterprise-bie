import unittest,tempfile,sqlite3,subprocess,sys,json
from pathlib import Path
from copy import deepcopy
from batch005_helpers import cohort,rehash,trust,token,NOW,ROOT
from bie.evaluation.benchmarks.models import BenchmarkError,digest,canonical_json
from bie.evaluation.benchmarks.release import gate
from bie.evaluation.benchmarks.release.ledger import ReleaseLedger
class ReleaseGate004(unittest.TestCase):
    def setUp(self):self.m,self.p,self.a=cohort()
    def run_gate(self,**kw):return gate.evaluate(self.m,self.p,self.a,expected_manifest_sha256=digest(self.m),expected_policy_sha256=digest(self.p),**kw)
    def test_complete_fixture_is_only_diagnostic_pass(self):
        o=self.run_gate();self.assertEqual('DIAGNOSTIC_PASS',o['outcome']);self.assertFalse(o['benchmark_gate_passed'])
    def test_no_deployment_or_product_authorization(self):
        o=self.run_gate();self.assertFalse(o['release_authorized']);self.assertFalse(o['product_accepted'])
    def test_missing_case_rater_blocks(self):self.a.pop();self.assertEqual('BLOCKED',self.run_gate()['outcome'])
    def test_missing_all_assessments_blocks(self):self.a=[];self.assertEqual('BLOCKED',self.run_gate()['outcome'])
    def test_one_low_case_blocks_even_high_others(self):
        self.a[0]['score_exact']='0';rehash(self.a[0]);self.assertEqual('BLOCKED',self.run_gate()['outcome'])
    def test_candidate_supplied_aggregate_not_accepted(self):
        self.a[0]['passed']=True
        with self.assertRaises(BenchmarkError):self.run_gate()
    def test_duplicate_assessment_rejects(self):
        self.a.append(deepcopy(self.a[0]))
        with self.assertRaisesRegex(BenchmarkError,'DUPLICATE_ASSESSMENT'):self.run_gate()
    def test_cross_candidate_assessment_rejects(self):
        self.a[0]['context']['candidate_sha256']=digest('elsewhere');rehash(self.a[0])
        with self.assertRaisesRegex(BenchmarkError,'CONTEXT_MISMATCH'):self.run_gate()
    def test_manifest_context_mismatch_rejects(self):
        self.m['dataset_sha256']=digest('elsewhere')
        with self.assertRaisesRegex(BenchmarkError,'MANIFEST_CONTEXT_MISMATCH'):self.run_gate()
    def test_production_policy_cannot_remove_attestations(self):
        self.p['mode']='PRODUCTION'
        with self.assertRaisesRegex(BenchmarkError,'PRODUCTION_ATTESTATION_POLICY_WEAKENED'):self.run_gate()
    def test_production_requires_all_seventeen_metrics(self):
        self.p['mode']='PRODUCTION';self.p['required_attestations']=sorted(gate.PRODUCTION_ATTESTATIONS)
        with self.assertRaisesRegex(BenchmarkError,'PRODUCTION_METRIC_COVERAGE_INCOMPLETE'):self.run_gate()
    def test_production_authored_reference_rejected(self):
        self.m,self.p,self.a=cohort(all_metrics=True);self.p['mode']='PRODUCTION';self.p['required_attestations']=sorted(gate.PRODUCTION_ATTESTATIONS)
        with self.assertRaisesRegex(BenchmarkError,'PRODUCTION_REFERENCE_GRADE_REQUIRED'):self.run_gate()
    def test_production_missing_evidence_blocks_not_pass(self):
        self.m,self.p,self.a=cohort(all_metrics=True,production=True);o=self.run_gate();self.assertEqual('BLOCKED',o['outcome']);self.assertIn('MISSING_NATIVE_BOOK_E2E',o['reasons'])
    def test_core_floor_cannot_be_weakened(self):
        self.m,self.p,self.a=cohort(all_metrics=True,production=True);self.p['critical_floors']['floors'][0]['minimum']='9/10'
        with self.assertRaisesRegex(BenchmarkError,'PRODUCTION_HARD_FLOOR_WEAKENED'):self.run_gate()
    def test_production_coverage_cannot_be_weakened(self):
        self.m,self.p,self.a=cohort(all_metrics=True,production=True);self.p['enterprise']['minimum_measured_fraction']='1/2'
        with self.assertRaisesRegex(BenchmarkError,'PRODUCTION_COVERAGE_WEAKENED'):self.run_gate()
    def test_undefined_kappa_not_silently_perfect(self):
        self.p['agreement']['minimum_kappa']='1/2';self.assertIn('KAPPA_REQUIREMENT_NOT_MET',self.run_gate()['reasons'])
    def test_required_external_attestation_missing_blocks(self):
        self.p['required_attestations']=['POLICY_APPROVAL'];self.assertIn('MISSING_POLICY_APPROVAL',self.run_gate()['reasons'])
    def signed_evidence(self):
        self.p['required_attestations']=['POLICY_APPROVAL'];scope=gate.evidence_scope(self.m,self.p,self.a)
        blob={'type':'AUTHORED_TEST_ONLY','evidence':'Local gate validation, not a real policy approval'}
        t=token('POLICY_APPROVAL',scope,{'outcome':'PASS','evidence_sha256':digest(blob)})
        return t,trust(roles=['POLICY_APPROVAL']),{digest(blob):blob}
    def test_scoped_diagnostic_attestation_verified(self):
        t,tr,blobs=self.signed_evidence();o=self.run_gate(attestations=[t],trust=tr,artifacts=blobs,now=NOW);self.assertEqual('DIAGNOSTIC_PASS',o['outcome'])
    def test_valid_signature_without_evidence_bytes_blocks(self):
        t,tr,_=self.signed_evidence();self.assertIn('ATTESTED_EVIDENCE_BYTES_MISSING',self.run_gate(attestations=[t],trust=tr,now=NOW)['reasons'])
    def test_attestation_cannot_be_reused_for_other_policy(self):
        t,tr,blobs=self.signed_evidence();self.p['version']='1.0.1';self.assertIn('ATTESTATION_SCOPE_MISMATCH',self.run_gate(attestations=[t],trust=tr,artifacts=blobs,now=NOW)['reasons'])
    def test_revoked_release_attestor_blocks(self):
        t,tr,blobs=self.signed_evidence();tr['test-key']['revoked']=True;self.assertIn('UNAUTHORIZED_ATTESTOR',self.run_gate(attestations=[t],trust=tr,artifacts=blobs,now=NOW)['reasons'])
    def test_duplicate_attestation_rejects(self):
        t,tr,blobs=self.signed_evidence()
        with self.assertRaisesRegex(BenchmarkError,'DUPLICATE_RELEASE_ATTESTATION'):self.run_gate(attestations=[t,t],trust=tr,artifacts=blobs,now=NOW)
    def test_report_hash_integrity(self):
        o=self.run_gate();self.assertEqual(digest({k:v for k,v in o.items() if k!='report_sha256'}),o['report_sha256'])
    def test_gate_order_independent(self):
        first=self.run_gate();self.a.reverse();self.assertEqual(first,self.run_gate())
    def test_bad_manifest_pin_rejects(self):
        with self.assertRaises(BenchmarkError):gate.evaluate(self.m,self.p,self.a,expected_manifest_sha256='0'*64,expected_policy_sha256=digest(self.p))
    def test_same_domain_dropped_from_policy_rejects(self):
        self.p['domains']['domains'].pop()
        with self.assertRaisesRegex(BenchmarkError,'DOMAIN_POLICY_ROSTER_MISMATCH'):self.run_gate()
class ReleaseLedger004(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'release.sqlite3';self.ledger=ReleaseLedger(self.path);self.m,self.p,self.a=cohort()
    def tearDown(self):self.ledger.close();self.tmp.cleanup()
    def execute(self,attempt='attempt1',campaign='campaign1'):
        return self.ledger.execute(campaign_id=campaign,attempt_id=attempt,manifest=self.m,policy=self.p,assessments=self.a,expected_manifest_sha256=digest(self.m),expected_policy_sha256=digest(self.p))
    def test_persisted_receipt_reopened(self):
        o=self.execute()
        with ReleaseLedger(self.path) as db:self.assertEqual(o,db.get('attempt1'))
    def test_same_artifact_attempt_cannot_be_retried(self):
        self.execute()
        with self.assertRaisesRegex(BenchmarkError,'ALREADY_RECORDED'):self.execute(attempt='retry')
    def test_failed_attempt_also_consumed(self):
        self.a=[];self.assertEqual('BLOCKED',self.execute()['report']['outcome'])
        with self.assertRaisesRegex(BenchmarkError,'ALREADY_RECORDED'):self.execute(attempt='retry')
    def test_policy_change_fails_campaign_freeze(self):
        self.execute();self.p['version']='1.0.1'
        with self.assertRaisesRegex(BenchmarkError,'CAMPAIGN_CHANGED'):self.execute(attempt='second')
    def test_distinct_artifact_same_pinned_campaign_supported(self):
        self.execute();self.m['artifact_sha256']=digest('artifact2');self.assertEqual('DIAGNOSTIC_PASS',self.execute(attempt='second')['report']['outcome'])
    def test_candidate_revision_does_not_change_pinned_roster(self):
        self.execute();self.m['artifact_sha256']=digest('artifact2')
        self.m['cases'][0]['context']['candidate_sha256']=digest('new')
        for row in self.a:
            if row['context']['case_id']=='case1':row['context']['candidate_sha256']=digest('new');rehash(row)
        self.assertEqual('DIAGNOSTIC_PASS',self.execute(attempt='second')['report']['outcome'])
    def test_roster_change_not_silent_new_campaign(self):
        self.execute();self.m['cases'][0]['leakage_group']='changed'
        with self.assertRaisesRegex(BenchmarkError,'CAMPAIGN_CHANGED'):self.execute(attempt='second')
    def test_invalid_policy_keeps_blocked_receipt(self):
        self.p['mode']='PRODUCTION';o=self.execute();self.assertEqual('BLOCKED',o['report']['outcome']);self.assertEqual(o,self.ledger.get('attempt1'))
    def test_tampered_receipt_detected(self):
        self.execute();self.ledger.db.execute("UPDATE release_attempts SET receipt='{}'")
        with self.assertRaisesRegex(BenchmarkError,'INTEGRITY'):self.ledger.get('attempt1')
    def test_corrupt_campaign_binding_detected(self):
        self.execute();self.ledger.db.execute("UPDATE release_campaigns SET binding='{}'")
        with self.assertRaises(BenchmarkError):self.ledger.get('attempt1')
    def test_incomplete_attempt_not_success(self):
        self.execute();self.ledger.db.execute("UPDATE release_attempts SET state='RUNNING'")
        with self.assertRaisesRegex(BenchmarkError,'INCOMPLETE'):self.ledger.get('attempt1')
    def test_unknown_attempt_not_success(self):
        with self.assertRaisesRegex(BenchmarkError,'UNKNOWN_RELEASE_ATTEMPT'):self.ledger.get('missing')
    def test_symlink_database_refused(self):
        link=self.path.parent/'link.sqlite3';link.symlink_to(self.path)
        with self.assertRaisesRegex(BenchmarkError,'SYMLINK_REFUSED'):ReleaseLedger(link)
    def test_symlink_parent_refused(self):
        link=self.path.parent/'linkdir';link.symlink_to(self.path.parent,target_is_directory=True)
        with self.assertRaisesRegex(BenchmarkError,'SYMLINK_REFUSED'):ReleaseLedger(link/'new.sqlite3')
    def test_database_directory_refused(self):
        with self.assertRaisesRegex(BenchmarkError,'INVALID_LEDGER_PATH'):ReleaseLedger(self.path.parent)
