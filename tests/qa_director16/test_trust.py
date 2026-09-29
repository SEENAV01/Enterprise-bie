from dir_helpers import *

class Trust(FixtureCase):
    def reviewed(self, **changes):
        reviews=list(signed_reviews(self.request,self.policy));reviews[0]=sign(replace(reviews[0],**changes),key());return tuple(reviews)
    def test_missing_review_blocks_pass(self):
        self.assertCode(self.run_check(reviews=()),'script','DIR_REVIEW_QUORUM_MISSING','REVIEW_REQUIRED')
    def test_wrong_request_digest(self):
        self.assertCode(self.run_check(reviews=self.reviewed(request_digest='a'*64)),'script','REVIEW_REQUEST_MISMATCH')
    def test_wrong_policy_digest(self):
        self.assertCode(self.run_check(reviews=self.reviewed(policy_digest='a'*64)),'script','REVIEW_POLICY_MISMATCH')
    def test_stale_review(self):
        self.assertCode(self.run_check(reviews=self.reviewed(issued_at=NOW-100,expires_at=NOW)),'script','REVIEW_TIME_INVALID')
    def test_future_review(self):
        self.assertCode(self.run_check(reviews=self.reviewed(issued_at=NOW+1,expires_at=NOW+100)),'script','REVIEW_TIME_INVALID')
    def test_excessive_lifetime(self):
        self.assertCode(self.run_check(reviews=self.reviewed(issued_at=NOW-10,expires_at=NOW+90000)),'script','REVIEW_LIFETIME_EXCEEDED')
    def test_unknown_key(self):
        self.assertCode(self.run_check(verifier=ReviewVerifier()),'script','UNKNOWN_REVIEW_KEY')
    def test_revoked_key(self):
        self.assertCode(self.run_check(verifier=ReviewVerifier((key(enabled=False),))),'script','REVOKED_REVIEW_KEY')
    def test_wrong_reviewer_version(self):
        self.assertCode(self.run_check(reviews=self.reviewed(evaluator_version='different')),'script','UNAUTHORIZED_REVIEWER')
    def test_corrupted_signature(self):
        rr=list(signed_reviews(self.request,self.policy));rr[0]=replace(rr[0],signature='0'*64)
        self.assertCode(self.run_check(reviews=tuple(rr)),'script','BAD_REVIEW_SIGNATURE')
    def test_unknown_subject(self):
        self.assertCode(self.run_check(reviews=self.reviewed(subject_id='unknown')),'script','DIR_UNKNOWN_REVIEW_TARGET')
    def test_wrong_evidence_inventory(self):
        self.assertCode(self.run_check(reviews=self.reviewed(evidence_ids=('unrelated',))),'script','DIR_REVIEW_EVIDENCE_MISMATCH')
    def test_test_key_not_operational(self):
        self.assertCode(self.run_check(verifier=ReviewVerifier((key(assurance='test_only'),))),'script','DIR_TEST_ONLY_REVIEW','REVIEW_REQUIRED')
    def test_uncertain_review(self):
        self.assertCode(self.run_check(reviews=self.reviewed(verdict='UNCERTAIN')),'script','DIR_REVIEW_UNCERTAIN','REVIEW_REQUIRED')
    def test_low_confidence(self):
        self.assertCode(self.run_check(reviews=self.reviewed(confidence_ppm=899999)),'script','DIR_REVIEW_UNCERTAIN','REVIEW_REQUIRED')
    def test_rejection_is_blocker(self):
        self.assertCode(self.run_check(reviews=self.reviewed(verdict='REJECTED')),'script','DIR_REVIEW_REJECTED','BLOCKED')
    def test_duplicate_id_rejected(self):
        rr=signed_reviews(self.request,self.policy)
        with self.assertRaisesRegex(ContractError,'DIR_DUPLICATE_REVIEW_ID'):self.run_check(reviews=rr+(rr[0],))
    def test_duplicate_reviewer_vote_rejected(self):
        rr=signed_reviews(self.request,self.policy)
        with self.assertRaisesRegex(ContractError,'DIR_DUPLICATE_REVIEW_VOTE'):self.run_check(reviews=rr+(replace(rr[0],review_id='other-id'),))
    def test_two_assessors_same_group_not_independent(self):
        k2=key(key_id='dir-key-two',evaluator_id='assessor-two',secret=b'SYNTHETIC_SECOND_SECRET_NOT_PRODUCTION_002')
        p=replace(self.policy,minimum_independent_assessors=2)
        rr=signed_reviews(self.request,p)+signed_reviews(self.request,p,k2)
        self.assertCode(self.run_check(p=p,reviews=rr,verifier=ReviewVerifier((key(),k2))),'script','DIR_REVIEW_QUORUM_MISSING','REVIEW_REQUIRED')
    def test_two_independent_synthetic_keys_can_satisfy_test_quorum(self):
        k2=key(key_id='dir-key-two',evaluator_id='assessor-two',independence_group='group-two',secret=b'SYNTHETIC_SECOND_SECRET_NOT_PRODUCTION_002')
        p=replace(self.policy,minimum_independent_assessors=2)
        rr=signed_reviews(self.request,p)+signed_reviews(self.request,p,k2)
        self.assertEqual(self.run_check(p=p,reviews=rr,verifier=ReviewVerifier((key(),k2))).status,'CHECKS_PASSED')
    def test_rejection_cannot_be_outvoted(self):
        k2=key(key_id='dir-key-two',evaluator_id='assessor-two',independence_group='group-two',secret=b'SYNTHETIC_SECOND_SECRET_NOT_PRODUCTION_002')
        rr=self.reviewed(verdict='REJECTED')+signed_reviews(self.request,self.policy,k2)
        self.assertCode(self.run_check(reviews=rr,verifier=ReviewVerifier((key(),k2))),'script','DIR_REVIEW_REJECTED','BLOCKED')
    def test_shared_secret_not_independence(self):
        with self.assertRaisesRegex(ContractError,'SHARED_SECRET_NOT_INDEPENDENT'):
            ReviewVerifier((key(),key(key_id='other-key',evaluator_id='other',independence_group='other')))
    def test_source_reviews_still_required(self):
        self.assertEqual(self.run_check(source_assessments=()).status,'REVIEW_REQUIRED')
    def test_review_change_invalidates_digest(self):
        base=self.run_check().content_digest
        rr=self.reviewed(rationale='Different synthetic rationale.')
        self.assertNotEqual(self.run_check(reviews=rr).content_digest,base)
    def test_canonical_order_change_invalidates_existing_review(self):
        r=replace(self.request,beats=tuple(reversed(self.request.beats)))
        self.assertCode(self.run_check(r,reviews=signed_reviews(self.request,self.policy)),'script','REVIEW_REQUEST_MISMATCH')
