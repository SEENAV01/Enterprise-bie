from ped_helpers import *

class TrustTests(FixtureCase):
 def edited_review(self,**changes):
  vals=list(signed_reviews(self.request,self.policy));vals[0]=sign(replace(vals[0],**changes),key());return tuple(vals)
 def test_missing_contextual_teaching_review(self):
  vals=tuple(a for a in signed_reviews(self.request,self.policy) if a.subject_id!='teach-1')
  self.assertCode(self.run_check(reviews=vals),'objectives','REVIEW_QUORUM_MISSING','REVIEW_REQUIRED')
 def test_missing_answer_correctness_review(self):
  vals=tuple(a for a in signed_reviews(self.request,self.policy) if (a.purpose,a.subject_id)!=('support','item-1'))
  self.assertCode(self.run_check(reviews=vals),'assessment','REVIEW_QUORUM_MISSING','REVIEW_REQUIRED')
 def test_missing_load_profile_review(self):
  vals=tuple(a for a in signed_reviews(self.request,self.policy) if a.subject_id!='load-policy')
  self.assertCode(self.run_check(reviews=vals),'cognitive_load','REVIEW_QUORUM_MISSING','REVIEW_REQUIRED')
 def test_missing_route_inventory_review(self):
  vals=tuple(a for a in signed_reviews(self.request,self.policy) if a.subject_id!='core-route')
  self.assertCode(self.run_check(reviews=vals),'sequence','REVIEW_QUORUM_MISSING')
 def test_bad_signature_blocks(self):
  vals=list(signed_reviews(self.request,self.policy));vals[0]=replace(vals[0],signature='0'*64)
  self.assertCode(self.run_check(reviews=tuple(vals)),'objectives','BAD_REVIEW_SIGNATURE')
 def test_wrong_request_binding(self):self.assertCode(self.run_check(reviews=self.edited_review(request_digest='0'*64)),'objectives','REVIEW_REQUEST_MISMATCH')
 def test_wrong_policy_binding(self):self.assertCode(self.run_check(reviews=self.edited_review(policy_digest='0'*64)),'objectives','REVIEW_POLICY_MISMATCH')
 def test_future_receipt(self):self.assertCode(self.run_check(reviews=self.edited_review(issued_at=NOW+1)),'objectives','REVIEW_TIME_INVALID')
 def test_expired_receipt(self):self.assertCode(self.run_check(reviews=self.edited_review(expires_at=NOW)),'objectives','REVIEW_TIME_INVALID')
 def test_excessive_lifetime(self):self.assertCode(self.run_check(reviews=self.edited_review(issued_at=NOW-604801)),'objectives','REVIEW_LIFETIME_EXCEEDED')
 def test_unknown_key(self):self.assertCode(self.run_check(reviews=self.edited_review(key_id='unknown')),'objectives','UNKNOWN_REVIEW_KEY')
 def test_revoked_key(self):self.assertCode(self.run_check(verifier=ReviewVerifier((key(enabled=False),))),'objectives','REVOKED_REVIEW_KEY')
 def test_reviewer_identity(self):self.assertCode(self.run_check(reviews=self.edited_review(evaluator_id='imposter')),'objectives','UNAUTHORIZED_REVIEWER')
 def test_reviewer_version(self):self.assertCode(self.run_check(reviews=self.edited_review(evaluator_version='2')),'objectives','UNAUTHORIZED_REVIEWER')
 def test_purpose_scoping(self):self.assertCode(self.run_check(verifier=ReviewVerifier((key(purposes=('inventory',)),))),'objectives','UNAUTHORIZED_REVIEW_PURPOSE')
 def test_wrong_evidence_scope(self):self.assertCode(self.run_check(reviews=self.edited_review(evidence_ids=('unrelated',))),'objectives','REVIEW_EVIDENCE_SCOPE_MISMATCH')
 def test_unknown_review_subject(self):self.assertCode(self.run_check(reviews=self.edited_review(subject_id='unknown')),'objectives','UNKNOWN_REVIEW_SUBJECT')
 def test_rejection_blocks(self):self.assertCode(self.run_check(reviews=self.edited_review(verdict='REJECTED')),'objectives','REVIEW_REJECTED','BLOCKED')
 def test_uncertainty_requires_review(self):self.assertCode(self.run_check(reviews=self.edited_review(verdict='UNCERTAIN')),'objectives','REVIEW_UNCERTAIN_OR_LOW_CONFIDENCE','REVIEW_REQUIRED')
 def test_low_confidence_requires_review(self):self.assertCode(self.run_check(reviews=self.edited_review(confidence_ppm=899999)),'objectives','REVIEW_UNCERTAIN_OR_LOW_CONFIDENCE')
 def test_test_only_assurance_no_pass(self):
  self.assertCode(self.run_check(verifier=ReviewVerifier((key(assurance='test_only'),))),'objectives','TEST_ONLY_REVIEW','REVIEW_REQUIRED')
 def test_duplicate_review_id_rejected(self):
  vals=signed_reviews(self.request,self.policy)
  with self.assertRaises(ContractError):self.run_check(reviews=vals+(vals[0],))
 def test_duplicate_reviewer_vote_rejected(self):
  vals=signed_reviews(self.request,self.policy)
  with self.assertRaises(ContractError):self.run_check(reviews=vals+(sign(replace(vals[0],review_id='alias-review'),key()),))
 def test_independent_quorum_missing(self):
  p=replace(self.policy,minimum_independent_assessors=2)
  self.assertCode(self.run_check(p=p),'objectives','REVIEW_QUORUM_MISSING')
 def second_key(self,**kw):return key(key_id='second',evaluator_id='second-assessor',secret=b'SYNTHETIC_OTHER_PED_KEY_NOT_PRODUCTION_002',independence_group='other-group',**kw)
 def test_independent_quorum_success(self):
  p=replace(self.policy,minimum_independent_assessors=2);k=self.second_key()
  vals=signed_reviews(self.request,p)+signed_reviews(self.request,p,k)
  self.assertEqual(self.run_check(p=p,reviews=vals,verifier=ReviewVerifier((key(),k))).status,'CHECKS_PASSED')
 def test_same_lineage_does_not_make_quorum(self):
  p=replace(self.policy,minimum_independent_assessors=2);k=replace(self.second_key(),independence_group='ped-review-group')
  vals=signed_reviews(self.request,p)+signed_reviews(self.request,p,k)
  self.assertCode(self.run_check(p=p,reviews=vals,verifier=ReviewVerifier((key(),k))),'objectives','REVIEW_QUORUM_MISSING')
 def test_rejection_not_outvoted(self):
  k=self.second_key();other=list(signed_reviews(self.request,self.policy,k));other[0]=sign(replace(other[0],verdict='REJECTED'),k)
  vals=signed_reviews(self.request,self.policy)+tuple(other)
  self.assertCode(self.run_check(reviews=vals,verifier=ReviewVerifier((key(),k))),'objectives','REVIEW_REJECTED')
 def test_source_reviews_are_separate_obligations(self):
  x=self.run_check(source_assessments=());self.assertEqual(x.status,'REVIEW_REQUIRED')
 def test_policy_edit_invalidates_existing_receipts(self):
  vals=signed_reviews(self.request,self.policy)
  self.assertCode(self.run_check(p=self.limit(max_visual_units=5),reviews=vals),'cognitive_load','REVIEW_POLICY_MISMATCH')
 def test_shared_secret_cannot_fake_independence(self):
  with self.assertRaises(ContractError):ReviewVerifier((key(),replace(self.second_key(),secret=key().secret)))
 def test_no_acceptance_override_field(self):
  from bie.qa.pedagogy_v2.codec import request_from_dict
  data=asdict(self.request);data['accepted']=True
  with self.assertRaises(ContractError):request_from_dict(data)
