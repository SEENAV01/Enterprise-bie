from audit_helpers import *

class RegressionTests(AuditFixture):
    def test_baseline_failure_and_corrected_candidate_observed(self):
        d=inspect_regression(self.reg,self.snapshot,self.p,self.policy,self.ap,as_of=NOW)
        self.assertFalse(d['problems']);self.assertEqual(d['target_count'],1)
        self.assertEqual(self.reg['baseline']['checks'][1]['cases'][0]['status'],'FAIL')
        self.assertEqual(self.reg['candidate']['checks'][1]['cases'][0]['status'],'PASS')
    def test_new_regression_detected_despite_successful_target(self):
        self.edit_regression(lambda x:x['candidate']['checks'][2]['cases'][0].update(status='FAIL',diagnostics=['CAPTION_REGRESSION']))
        self.assertCode('AUDIT_NEW_REGRESSION')
    def test_no_vacuous_repair_when_target_already_passed(self):
        self.edit_regression(lambda x:x['baseline']['checks'][1]['cases'][0].update(status='PASS',diagnostics=[]))
        self.assertCode('AUDIT_TARGET_FAILURE_NOT_REPRODUCED')
    def test_target_still_fails(self):
        self.edit_regression(lambda x:x['candidate']['checks'][1]['cases'][0].update(status='FAIL',diagnostics=['WRONG_SUM']))
        self.assertCode('AUDIT_TARGET_NOT_FIXED')
    def test_every_nonpass_status_is_rejected(self):
        for status in ('FAIL','REVIEW','NOT_RUN','ERROR'):
            with self.subTest(status=status):
                self.edit_regression(lambda x:x['candidate']['checks'][2]['cases'][0].update(status=status,diagnostics=['REASON']))
                self.assertCode('AUDIT_CANDIDATE_CASE_NOT_PASS')
    def test_missing_case_rejected(self):
        self.edit_regression(lambda x:x['candidate']['checks'][1].update(cases=[]));self.assertCode('AUDIT_CASE_COVERAGE')
    def test_duplicate_case_rejected(self):
        self.edit_regression(lambda x:x['candidate']['checks'][1]['cases'].append(x['candidate']['checks'][1]['cases'][0]))
        self.assertCode('AUDIT_CASE_COVERAGE')
    def test_renamed_case_rejected(self):
        self.edit_regression(lambda x:x['candidate']['checks'][1]['cases'][0].update(case_id='other'));self.assertCode('AUDIT_CASE_COVERAGE')
    def test_missing_check_rejected(self):
        self.edit_regression(lambda x:x['candidate']['checks'].pop());self.assertCode('AUDIT_REGRESSION_CHECK_COVERAGE')
    def test_reordered_checks_rejected(self):
        self.edit_regression(lambda x:x['candidate']['checks'].reverse());self.assertCode('AUDIT_REGRESSION_CHECK_ORDER')
    def test_validator_change_rejected(self):
        self.edit_regression(lambda x:x['candidate']['checks'][1].update(validator_digest='0'*64));self.assertCode('AUDIT_VALIDATOR_DRIFT')
    def test_fixture_byte_change_rejected(self):
        self.edit_regression(lambda x:x['fixture_manifest'][0].update(sha256='0'*64));self.assertCode('AUDIT_FIXTURE_BYTES')
    def test_fixture_scope_change_rejected(self):
        self.edit_regression(lambda x:x['candidate']['checks'][1].update(fixture_ids=['caption']));self.assertCode('AUDIT_CHECK_FIXTURE_SCOPE')
    def test_reused_execution_rejected(self):
        self.edit_regression(lambda x:x['candidate'].update(execution_id=x['baseline']['execution_id']));self.assertCode('AUDIT_REUSED_EXECUTION')
    def test_wrong_snapshot_rejected(self):
        self.edit_regression(lambda x:x['candidate'].update(snapshot_digest=x['baseline']['snapshot_digest']));self.assertCode('AUDIT_RUN_SNAPSHOT')
    def test_wrong_policy_binding_rejected(self):
        self.edit_regression(lambda x:x['binding'].update(repair_policy_digest='0'*64));self.assertCode('AUDIT_REGRESSION_BINDING')
    def test_environment_hash_recomputed(self):
        self.edit_regression(lambda x:x['environment'].update(python_version='other'));self.assertCode('AUDIT_ENVIRONMENT_DIGEST')
    def test_nonexecution_rejected(self):
        self.edit_regression(lambda x:x['candidate'].update(worker_executed=False));self.assertCode('AUDIT_REGRESSION_NOT_EXECUTED')
    def test_worker_error_rejected(self):
        self.edit_regression(lambda x:x['candidate'].update(error='timeout'));self.assertCode('AUDIT_REGRESSION_WORKER_ERROR')
    def test_stale_detail_record_rejected(self):
        self.edit_regression(lambda x:x.update(evaluated_at=NOW-3601));self.assertCode('AUDIT_REGRESSION_STALE')
    def test_future_record_rejected(self):
        self.edit_regression(lambda x:x['candidate'].update(executed_at=NOW+1));self.assertCode('AUDIT_RUN_STALE')
    def test_predating_repair_rejected(self):
        self.edit_regression(lambda x:x.update(evaluated_at=NOW-1));self.assertCode('AUDIT_REGRESSION_PREDATES_REPAIR')
    def test_false_full_repository_claim_rejected(self):
        self.edit_regression(lambda x:x.update(full_repository_regression_run=True));self.assertCode('AUDIT_REGRESSION_SCOPE')
    def test_missing_witness_rejected(self):
        self.edit_regression(lambda x:x['candidate']['checks'][0]['cases'][0].update(witness='{}'));self.assertCode('AUDIT_CASE_WITNESS')
