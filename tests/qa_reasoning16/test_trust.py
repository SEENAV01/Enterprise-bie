from dataclasses import replace
from re_helpers import *
from bie.qa.reasoning_v2.attestation import PURPOSES

class TrustTests(FixtureCase):
    def test_default_no_keys_no_pass(self):
        r=evaluate(self.request,self.root,self.policy,as_of=NOW);self.assertNotEqual(r.status,'CHECKS_PASSED')
    def test_bad_signature(self):
        opts=options(self.request,self.policy);v=list(opts['reviews']);v[0]=replace(v[0],signature='0'*64);opts['reviews']=tuple(v)
        self.assertCode(self.run_check(**opts),'validity','BAD_REVIEW_SIGNATURE')
    def test_stale_request_signature(self):
        opts=options(self.request,self.policy);r=replace(self.request,decisions=(replace(self.request.decisions[0],confidence_ppm=940000),))
        self.assertCode(self.run_check(r,**opts),'validity','REVIEW_REQUEST_MISMATCH')
    def test_policy_replay(self):
        opts=options(self.request,self.policy);p=replace(self.policy,policy_id='policy-new');self.assertCode(self.run_check(policy=p,**opts),'validity','REVIEW_POLICY_MISMATCH')
    def test_revoked_key(self):self.assertCode(self.run_check(verifier=ReviewVerifier((key(enabled=False),))),'validity','REVOKED_REVIEW_KEY')
    def test_unknown_key(self):self.assertCode(self.run_check(verifier=ReviewVerifier()),'validity','UNKNOWN_REVIEW_KEY')
    def test_wrong_evaluator(self):self.assertCode(self.run_check(verifier=ReviewVerifier((key(evaluator_id='imposter'),))),'validity','UNAUTHORIZED_REVIEWER')
    def test_wrong_version(self):self.assertCode(self.run_check(verifier=ReviewVerifier((key(evaluator_version='2'),))),'validity','UNAUTHORIZED_REVIEWER')
    def test_wrong_purpose(self):self.assertCode(self.run_check(verifier=ReviewVerifier((key(purposes=('support',)),))),'validity','UNAUTHORIZED_REVIEW_PURPOSE')
    def modify_review(self,**changes):
        opts=options(self.request,self.policy);v=list(opts['reviews']);v[0]=sign(replace(v[0],**changes),key());opts['reviews']=tuple(v);return opts
    def test_expired(self):self.assertCode(self.run_check(**self.modify_review(expires_at=NOW)),'validity','REVIEW_TIME_INVALID')
    def test_future(self):self.assertCode(self.run_check(**self.modify_review(issued_at=NOW+1)),'validity','REVIEW_TIME_INVALID')
    def test_lifetime_limit(self):self.assertCode(self.run_check(**self.modify_review(expires_at=NOW+604800)),'validity','REVIEW_LIFETIME_EXCEEDED')
    def test_wrong_evidence_scope(self):self.assertCode(self.run_check(**self.modify_review(evidence_ids=('missing',))),'validity','REVIEW_EVIDENCE_SCOPE_MISMATCH')
    def test_unknown_subject(self):self.assertCode(self.run_check(**self.modify_review(subject_id='missing')),'validity','UNKNOWN_REVIEW_SUBJECT')
    def test_test_keys_cannot_promote(self):
        k=key(assurance='test_only');r=self.run_check(reviews=signed_reviews(self.request,self.policy,k),verifier=ReviewVerifier((k,)))
        self.assertCode(r,'validity','TEST_ONLY_REVIEW');self.assertNotEqual(r.status,'CHECKS_PASSED')
    def test_duplicate_review_id(self):
        opts=options(self.request,self.policy);opts['reviews']+=opts['reviews'][:1]
        with self.assertRaises(ContractError):self.run_check(**opts)
    def test_duplicate_principal_vote(self):
        opts=options(self.request,self.policy);opts['reviews']+=(sign(replace(opts['reviews'][0],review_id='new-id'),key()),)
        with self.assertRaises(ContractError):self.run_check(**opts)
    def test_quorum_not_satisfied_by_same_independence_group(self):
        p=replace(self.policy,minimum_independent_assessors=2);k2=key(key_id='key2',secret=b'SECOND_SYNTHETIC_KEY_NEVER_DEPLOY_0002',evaluator_id='second-assessor')
        r=self.run_check(policy=p,reviews=signed_reviews(self.request,p)+signed_reviews(self.request,p,k2),verifier=ReviewVerifier((key(),k2)))
        self.assertCode(r,'validity','REVIEW_QUORUM_MISSING')
    def test_two_independent_reviewers(self):
        p=replace(self.policy,minimum_independent_assessors=2);k2=key(key_id='key2',secret=b'SECOND_SYNTHETIC_KEY_NEVER_DEPLOY_0002',evaluator_id='second-assessor',independence_group='independent-b')
        r=self.run_check(policy=p,reviews=signed_reviews(self.request,p)+signed_reviews(self.request,p,k2),verifier=ReviewVerifier((key(),k2)))
        self.assertEqual(r.status,'CHECKS_PASSED')
    def test_negative_reviewer_not_outvoted(self):
        k2=key(key_id='key2',secret=b'SECOND_SYNTHETIC_KEY_NEVER_DEPLOY_0002',evaluator_id='second-assessor',independence_group='independent-b')
        reviews=list(signed_reviews(self.request,self.policy,k2));reviews=[sign(replace(x,verdict='REJECTED'),k2) if x.purpose=='mapping' else x for x in reviews]
        r=self.run_check(reviews=signed_reviews(self.request,self.policy)+tuple(reviews),verifier=ReviewVerifier((key(),k2)))
        self.assertCode(r,'validity','REVIEW_REJECTED')
    def test_uncertain_vote_not_outvoted(self):
        k2=key(key_id='key2',secret=b'SECOND_SYNTHETIC_KEY_NEVER_DEPLOY_0002',evaluator_id='second-assessor',independence_group='independent-b')
        reviews=list(signed_reviews(self.request,self.policy,k2));reviews=[sign(replace(x,verdict='UNCERTAIN'),k2) if x.purpose=='mapping' else x for x in reviews]
        r=self.run_check(reviews=signed_reviews(self.request,self.policy)+tuple(reviews),verifier=ReviewVerifier((key(),k2)))
        self.assertCode(r,'validity','REVIEW_UNCERTAIN_OR_LOW_CONFIDENCE')
    def test_low_review_confidence(self):
        reviews=tuple(sign(replace(x,confidence_ppm=1),key()) for x in signed_reviews(self.request,self.policy));self.assertCode(self.run_check(reviews=reviews),'validity','REVIEW_UNCERTAIN_OR_LOW_CONFIDENCE')
    def test_shared_secret_cannot_claim_independence(self):
        with self.assertRaises(ContractError):ReviewVerifier((key(),key(key_id='new',evaluator_id='new',independence_group='different')))
    def test_principal_cannot_switch_independence_group(self):
        with self.assertRaises(ContractError):ReviewVerifier((key(),key(key_id='new',secret=b'SECOND_SYNTHETIC_KEY_NEVER_DEPLOY_0002',independence_group='different')))
    def test_duplicate_key(self):
        with self.assertRaises(ContractError):ReviewVerifier((key(),key()))
    def test_short_secret(self):
        with self.assertRaises(ContractError):key(secret=b'short')
    def test_secret_not_in_repr(self):self.assertNotIn(key().secret.decode(),repr(key()))
    def test_revocation_changes_configuration_identity(self):self.assertNotEqual(ReviewVerifier((key(),)).configuration_digest,ReviewVerifier((key(enabled=False),)).configuration_digest)
    def test_source_grounding_not_bypassed_by_reasoning_reviews(self):
        self.assertNotEqual(self.run_check(source_assessments=(),source_verifier=AssessmentVerifier()).status,'CHECKS_PASSED')
    def test_review_order_does_not_change_result(self):
        a=self.run_check();b=self.run_check(reviews=tuple(reversed(signed_reviews(self.request,self.policy))));self.assertEqual(a,b)

    def test_low_level_verifier_rejects_invalid_lifetime(self):
        review=signed_reviews(self.request,self.policy)[0]
        with self.assertRaises(ContractError):ReviewVerifier((key(),)).verify_bound(review,self.request.content_digest,self.policy.content_digest,True,NOW)
    def test_low_level_verifier_rejects_malformed_context_digest(self):
        review=signed_reviews(self.request,self.policy)[0]
        with self.assertRaises(ContractError):ReviewVerifier((key(),)).verify_bound(review,'garbled',self.policy.content_digest,60,NOW)
