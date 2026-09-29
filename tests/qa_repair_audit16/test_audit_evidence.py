from audit_helpers import *

class EvidenceTests(AuditFixture):
    def test_real_repair_audit_passes_bounded_checks(self):self.assertEqual(self.audit().status,'CHECKS_PASSED')
    def test_no_product_acceptance(self):
        r=self.audit().to_dict();self.assertFalse(r['product_accepted']);self.assertFalse(r['full_repository_regression_run'])
    def test_expected_change_and_cases(self):
        r=self.audit();self.assertEqual(r.changes,('lesson',));self.assertEqual(dict(r.regression.measurements)['case_pairs'],3)
    def test_originals_not_modified(self):
        self.audit();self.assertEqual((self.root/'generated/lesson.txt').read_bytes(),b'2+4')
    def test_repeat_evaluation_deterministic(self):self.assertEqual(self.audit().to_dict(),self.audit().to_dict())
    def test_missing_audit_authentication_requires_review(self):
        r=self.audit(audit_reviews=());self.assertEqual(r.status,'REVIEW_REQUIRED');self.assertCode('AUDIT_EXECUTION_AUTH_REQUIRED',r)
    def test_missing_inventory_authentication_requires_review(self):self.assertCode('AUDIT_INVENTORY_AUTH_REQUIRED',self.audit(inventory_reviews=()))
    def test_missing_proposal_authentication_requires_review(self):self.assertCode('AUDIT_PROPOSAL_AUTH_REQUIRED',self.audit(proposal_reviews=()))
    def test_old_signature_cannot_authenticate_edited_receipt(self):
        reviews=(audit_review(self.request,self.ap),)
        self.edit_regression(lambda d:d['environment'].update(note='changed'))
        self.reg['environment_digest']=digest(self.reg['environment'])
        self.request=replace(self.request,regression=self.put('audit/regression.json',self.reg,'regression'))
        self.assertCode('AUDIT_EXECUTION_AUTH_REQUIRED',self.audit(audit_reviews=reviews))
    def test_test_only_key_not_operational(self):
        k=replace(AUDIT_KEY,assurance='test_only');r=self.audit(audit_reviews=(audit_review(self.request,self.ap,key=k),),verifier=ReviewVerifier((KEY,k)))
        self.assertCode('AUDIT_EXECUTION_AUTH_REQUIRED',r)
    def test_rejected_review_cannot_be_outvoted(self):
        r=audit_review(self.request,self.ap);bad=replace(r,review_id='rejected',verdict='REJECTED',signature='')
        bad=replace(bad,signature=hmac.new(AUDIT_KEY.secret,bad.signing_bytes(),hashlib.sha256).hexdigest())
        self.assertCode('AUDIT_EXECUTION_AUTH_REQUIRED',self.audit(audit_reviews=(r,bad)))
    def test_duplicate_review_rejected(self):
        r=audit_review(self.request,self.ap);self.assertCode('REPAIR_DUPLICATE_REVIEW',self.audit(audit_reviews=(r,r)))
    def test_artifact_tampering_detected(self):
        p=self.root/self.request.attempt.path;p.write_bytes(p.read_bytes()+b' ');self.assertCode('ARTIFACT_SIZE_MISMATCH')
    def test_attempt_hash_recomputed(self):
        self.edit_attempt(lambda x:x.update(worker_elapsed_ms=x['worker_elapsed_ms']+1),rehash=False,rechain=False)
        self.assertCode('AUDIT_ATTEMPT_HASH')
    def test_extra_receipt_field_rejected(self):
        self.edit_attempt(lambda x:x.update(success=True));self.assertCode('AUDIT_ATTEMPT_SCHEMA')
    def test_attempt_schema_version_rejected(self):
        self.edit_attempt(lambda x:x.update(schema_version='unknown'));self.assertCode('AUDIT_ATTEMPT_VERSION')
    def test_wrong_proposal_receipt_rejected(self):
        self.edit_attempt(lambda x:x.update(proposal_digest='0'*64));self.assertCode('AUDIT_ATTEMPT_BINDING')
    def test_attempt_boolean_cannot_be_integer(self):
        self.edit_attempt(lambda x:x.update(worker_executed=1));self.assertCode('AUDIT_WORKER_NOT_EXECUTED')
    def test_nonexecuted_worker_cannot_pass(self):
        self.edit_attempt(lambda x:x.update(worker_executed=False));self.assertCode('AUDIT_WORKER_NOT_EXECUTED')
    def test_failed_worker_cannot_pass(self):
        self.edit_attempt(lambda x:x.update(worker_error='TIMEOUT'));self.assertCode('AUDIT_ATTEMPT_WORKER_ERROR')
    def test_hidden_attempt_diagnostic_rejected(self):
        self.edit_attempt(lambda x:x.update(diagnostics=['ERROR']));self.assertCode('AUDIT_ATTEMPT_DIAGNOSTICS')
    def test_all_scope_flags_fail_closed(self):
        for field in ('original_files_written','canonical_repository_modified','product_accepted','downstream_previous_evidence_reusable','hostile_code_sandbox_verified'):
            with self.subTest(field=field):
                saved=self.attempt.copy();self.edit_attempt(lambda x:x.update({field:True}));self.assertCode('AUDIT_ATTEMPT_SCOPE')
                self.attempt=saved;self.edit_attempt(lambda x:None)
    def test_candidate_inventory_cannot_drop_file(self):
        self.edit_attempt(lambda x:x['candidate']['artifacts'].pop());self.assertCode('AUDIT_CANDIDATE_INVENTORY')
    def test_candidate_digest_mismatch(self):
        self.edit_attempt(lambda x:x.update(candidate_digest='0'*64));self.assertCode('AUDIT_CANDIDATE_DIGEST')
    def test_required_check_omission(self):
        self.edit_attempt(lambda x:x['required_checks'].pop());self.assertCode('AUDIT_CHECK_CLOSURE')
    def test_invalidation_omission(self):
        self.edit_attempt(lambda x:x['invalidated_previous_checks'].pop());self.assertCode('AUDIT_INVALIDATION_CLOSURE')
    def test_outcome_omission(self):
        self.edit_attempt(lambda x:x['outcomes'].pop());self.assertCode('AUDIT_OUTCOME_COVERAGE')
    def test_outcome_wrong_candidate(self):
        self.edit_attempt(lambda x:x['outcomes'][0].update(candidate_digest='0'*64));self.assertCode('AUDIT_OUTCOME_BINDING')
    def test_nonpassing_staging_outcome(self):
        self.edit_attempt(lambda x:x['outcomes'][0].update(status='REVIEW',diagnostics=['UNCERTAIN']));self.assertCode('AUDIT_STAGED_OUTCOME_NOT_PASS')
    def test_hiding_remaining_failure_rejected(self):
        self.edit_attempt(lambda x:x.update(remaining_failure_ids=['invented']));self.assertCode('AUDIT_HIDDEN_UNRESOLVED_FAILURE')
    def test_staging_path_is_not_followed(self):
        self.edit_attempt(lambda x:x.update(staged_directory='/not-a-real-location'))
        self.assertEqual(self.audit().status,'CHECKS_PASSED')
    def test_empty_staging_path_rejected(self):
        self.edit_attempt(lambda x:x.update(staged_directory=''));self.assertCode('AUDIT_STAGED_DIRECTORY_MISSING')
    def test_actual_candidate_bytes_inspected(self):
        (self.candidate_root/'generated/lesson.txt').write_bytes(b'2+8');self.assertCode('ARTIFACT_HASH_MISMATCH')
    def test_extra_candidate_file_detected(self):
        (self.candidate_root/'extra.txt').write_text('extra');self.assertCode('AUDIT_SNAPSHOT_FILE_SET')
    def test_candidate_symlink_directory_detected(self):
        (self.candidate_root/'linked').symlink_to(self.root,target_is_directory=True);self.assertCode('AUDIT_UNSAFE_ENTRY')
    def test_candidate_hardlink_detected(self):
        os.link(self.candidate_root/'generated/lesson.txt',self.home/'hard');self.assertCode('AUDIT_UNSAFE_ENTRY')
    def test_original_source_modification_detected(self):
        (self.root/'sources/book.txt').write_bytes(b'damaged');self.assertCode('ARTIFACT_SIZE_MISMATCH')
    def test_generation_cannot_be_omitted_when_required(self):
        self.ap=replace(self.ap,require_generation=True);self.assertCode('AUDIT_GENERATION_REQUIRED')
