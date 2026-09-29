from repair_helpers import *

class ControllerTests(Fixture):
    def test_actual_staging_verified(self):
        r=self.run_proposal();self.assertEqual(r['status'],'STAGED_FOR_REVIEW');self.assertEqual((Path(r['staged_directory'])/'generated/lesson.txt').read_bytes(),b'2+3')
    def test_original_not_changed(self):r=self.run_proposal();self.assertEqual((self.root/'generated/lesson.txt').read_bytes(),b'2+4');self.assertFalse(r['original_files_written'])
    def test_no_release_acceptance(self):r=self.run_proposal();self.assertFalse(r['product_accepted']);self.assertFalse(r['downstream_previous_evidence_reusable'])
    def test_real_existing_math_checker(self):r=self.run_proposal();self.assertEqual([(x['check_id'],x['status']) for x in r['outcomes']],[('syntax','PASS'),('numeric','PASS'),('regression','PASS')])
    def test_wrong_math_rejected(self):r=self.run_proposal(self.proposal(b'2+8'));self.assertEqual(r['status'],'REJECTED');self.assertIn('REPAIR_REVALIDATION_NOT_PASS',r['diagnostics'])
    def test_bad_expression_rejected(self):r=self.run_proposal(self.proposal(b'('));self.assertEqual(r['status'],'REJECTED')
    def test_regression_cannot_be_hidden(self):
        p=self.proposal();a=self.write('bad-caption','proposals/caption.txt',b'caption changed');p=replace(p,replacements=p.replacements+(Replacement('generated/caption.txt',self.snapshot.artifacts[2].sha256,a),));r=self.run_proposal(p);self.assertEqual(r['status'],'REJECTED');self.assertEqual((self.root/'generated/caption.txt').read_bytes(),b'keep caption')
    def test_rejected_stage_cleaned(self):self.run_proposal(self.proposal(b'2+8'));self.assertEqual(list(self.out.iterdir()),[])
    def test_missing_verifier_blocks(self):self.assertRaises(ContractError,self.run_proposal,verifier=ReviewVerifier())
    def test_missing_proposal_approval(self):self.assertRaises(ContractError,self.run_proposal,proposal_reviews=())
    def test_missing_inventory_approval(self):self.assertRaises(ContractError,self.run_proposal,inventory_reviews=())
    def test_missing_required_check(self):self.assertRaises(ContractError,self.run_proposal,checks={'numeric':numeric_check})
    def test_no_op_rejected(self):self.assertRaises(ContractError,self.run_proposal,self.proposal(b'2+4'))
    def test_wrong_owner_rejected(self):self.assertRaises(ContractError,self.run_proposal,self.proposal(owner='GAME'))
    def test_unknown_failure_rejected(self):self.assertRaises(ContractError,self.run_proposal,self.proposal(target_failure_ids=('absent',)))
    def test_stale_base_rejected(self):self.assertRaises(ContractError,self.run_proposal,self.proposal(base_digest='b'*64))
    def test_wrong_policy_rejected(self):self.assertRaises(ContractError,self.run_proposal,self.proposal(policy_digest='c'*64))
    def test_wrong_plan_rejected(self):self.assertRaises(ContractError,self.run_proposal,self.proposal(plan_digest='c'*64))
    def test_wrong_run_rejected(self):self.assertRaises(ContractError,self.run_proposal,self.proposal(run_id='wrong'))
    def test_before_hash_rejected(self):p=self.proposal();p=replace(p,replacements=(replace(p.replacements[0],before_sha256='e'*64),));self.assertRaises(ContractError,self.run_proposal,p)
    def test_unowned_path_rejected(self):p=self.proposal();p=replace(p,replacements=(replace(p.replacements[0],path='generated/unowned.txt'),));self.assertRaises(ContractError,self.run_proposal,p)
    def test_protected_source_role_rejected(self):
        self.snapshot=replace(self.snapshot,artifacts=(self.snapshot.artifacts[0],replace(self.snapshot.artifacts[1],role='source'))+self.snapshot.artifacts[2:]);self.make_batch();self.assertRaises(ContractError,self.run_proposal)
    def test_replacement_tampering_rejected(self):p=self.proposal();(self.root/p.replacements[0].artifact.path).write_bytes(b'2+9');self.assertEqual(self.run_proposal(p)['status'],'REJECTED')
    def test_symlink_original_rejected(self):
        p=self.proposal();a=self.root/'generated/lesson.txt';a.unlink();a.symlink_to(self.root/'sources/book.txt');self.assertRaises(ContractError,self.run_proposal,p)
    def test_hardlink_replacement_rejected(self):
        p=self.proposal();a=self.root/p.replacements[0].artifact.path;os.link(a,self.root/'linked.txt');self.assertEqual(self.run_proposal(p)['status'],'REJECTED')
    def test_original_overlap_rejected(self):self.assertRaises(ContractError,self.run_proposal,output_root=self.root)
    def test_output_ancestor_rejected(self):self.assertRaises(ContractError,self.run_proposal,output_root=self.home)
    def test_check_exception_is_failure(self):r=self.run_proposal(checks={**self.checks,'numeric':exception_check});self.assertIn('REPAIR_CHECK_EXCEPTION',r['diagnostics']);self.assertEqual(r['status'],'REJECTED')
    def test_check_binding_rejected(self):r=self.run_proposal(checks={**self.checks,'numeric':wrong_binding});self.assertIn('REPAIR_CHECK_BINDING',r['diagnostics'])
    def test_check_wrong_id_rejected(self):r=self.run_proposal(checks={**self.checks,'numeric':wrong_check});self.assertIn('REPAIR_CHECK_COVERAGE',r['diagnostics'])
    def test_check_review_not_pass(self):r=self.run_proposal(checks={**self.checks,'numeric':review_check});self.assertEqual(r['status'],'REJECTED')
    def test_worker_mutation_detected(self):r=self.run_proposal(checks={'syntax':syntax_check,'numeric':mutate_stage,'regression':regression_check});self.assertEqual(r['status'],'REJECTED')
    def test_extra_file_detected(self):r=self.run_proposal(checks={**self.checks,'numeric':inject_extra});self.assertIn('REPAIR_STAGE_FILE_SET',r['diagnostics'])
    def test_hard_timeout(self):
        self.policy=replace(self.policy,worker_timeout_seconds=1);r=self.run_proposal(checks={**self.checks,'numeric':hang_check});self.assertIn('REPAIR_CHECK_TIMEOUT',r['diagnostics']);self.assertLess(r['worker_elapsed_ms'],3500)
    def test_all_prior_owner_descendants_invalidated(self):self.assertEqual(self.run_proposal()['invalidated_previous_checks'],('numeric','regression'))
    def test_no_mutable_repo_claim(self):r=self.run_proposal();self.assertFalse(r['canonical_repository_modified']);self.assertFalse(r['hostile_code_sandbox_verified'])
    def test_worker_recorded_not_simulated(self):self.assertTrue(self.run_proposal()['worker_executed'])
    def test_unsolved_other_failure_kept(self):
        self.make_batch(self.report.findings+(Finding('UNKNOWN_OTHER','REVIEW','other','QA','unresolved'),));r=self.run_proposal();self.assertEqual(len(r['remaining_failure_ids']),1)
    def test_failed_receipt_is_hashed(self):r=self.run_proposal(self.proposal(b'2+8'));b={k:v for k,v in r.items() if k not in ('receipt_digest','journal_head')};self.assertEqual(r['receipt_digest'],digest(b))
    def test_retry_can_succeed_with_new_proposal(self):self.run_proposal(self.proposal(b'2+8'));r=self.run_proposal(self.proposal(b'2+3',pid='second'));self.assertEqual(r['status'],'STAGED_FOR_REVIEW');self.assertEqual(r['attempt'],2)
