from math_helpers import *

class TrustTests(FixtureCase):
    def changed_review(self,**changes):
        rs=list(signed_reviews(self.request,self.policy));index=next(i for i,x in enumerate(rs) if x.subject_id=='formula-1');rs[index]=sign(replace(rs[index],**changes),key());return tuple(rs)
    def test_bad_signature(self):
        rs=list(signed_reviews(self.request,self.policy));rs[0]=replace(rs[0],signature='0'*64)
        self.assertEqual(self.run_check(reviews=tuple(rs)).status,'BLOCKED')
    def test_request_digest_binding(self):self.assertCode(self.run_check(reviews=self.changed_review(request_digest='0'*64)),'formula','REVIEW_REQUEST_MISMATCH','BLOCKED')
    def test_policy_digest_binding(self):self.assertCode(self.run_check(reviews=self.changed_review(policy_digest='0'*64)),'formula','REVIEW_POLICY_MISMATCH','BLOCKED')
    def test_expired_review(self):self.assertCode(self.run_check(reviews=self.changed_review(issued_at=NOW-100,expires_at=NOW)),'formula','REVIEW_TIME_INVALID')
    def test_future_review(self):self.assertCode(self.run_check(reviews=self.changed_review(issued_at=NOW+1,expires_at=NOW+100)),'formula','REVIEW_TIME_INVALID')
    def test_stale_review(self):self.assertCode(self.run_check(reviews=self.changed_review(issued_at=NOW-86401)),'formula','REVIEW_LIFETIME_EXCEEDED')
    def test_unknown_key(self):self.assertCode(self.run_check(reviews=self.changed_review(key_id='missing')),'formula','UNKNOWN_REVIEW_KEY')
    def test_revoked_key(self):self.assertEqual(self.run_check(verifier=ReviewVerifier((key(enabled=False),))).status,'BLOCKED')
    def test_test_only_authority_not_operational(self):self.assertCode(self.run_check(verifier=ReviewVerifier((key(assurance='test_only'),))),'formula','TEST_ONLY_REVIEW','REVIEW_REQUIRED')
    def test_no_keys_default_fail_closed(self):self.assertEqual(self.run_check(verifier=ReviewVerifier()).status,'BLOCKED')
    def test_assessor_version_binding(self):self.assertCode(self.run_check(reviews=self.changed_review(evaluator_version='2')),'formula','UNAUTHORIZED_REVIEWER')
    def test_unauthorized_purpose(self):self.assertCode(self.run_check(verifier=ReviewVerifier((key(purposes=('inventory',)),))),'formula','UNAUTHORIZED_REVIEW_PURPOSE')
    def test_rejected_review_blocks(self):self.assertCode(self.run_check(reviews=self.changed_review(verdict='REJECTED')),'formula','REVIEW_REJECTED','BLOCKED')
    def test_uncertain_review_not_pass(self):self.assertCode(self.run_check(reviews=self.changed_review(verdict='UNCERTAIN')),'formula','REVIEW_UNCERTAIN_OR_LOW_CONFIDENCE','REVIEW_REQUIRED')
    def test_low_confidence_not_pass(self):self.assertCode(self.run_check(reviews=self.changed_review(confidence_ppm=899999)),'formula','REVIEW_UNCERTAIN_OR_LOW_CONFIDENCE')
    def test_wrong_evidence_inventory(self):self.assertCode(self.run_check(reviews=self.changed_review(evidence_ids=('claim-2',))),'formula','REVIEW_EVIDENCE_SCOPE_MISMATCH')
    def test_unknown_subject(self):
        rs=list(signed_reviews(self.request,self.policy));rs[0]=sign(replace(rs[0],subject_id='ghost'),key());self.assertEqual(self.run_check(reviews=tuple(rs)).status,'BLOCKED')
    def test_duplicate_review_id(self):
        rs=signed_reviews(self.request,self.policy)
        with self.assertRaises(ContractError):self.run_check(reviews=rs+(rs[0],))
    def test_duplicate_reviewer_vote(self):
        rs=signed_reviews(self.request,self.policy)
        with self.assertRaises(ContractError):self.run_check(reviews=rs+(replace(rs[0],review_id='extra'),))
    def test_same_group_not_independent(self):
        p=replace(self.policy,minimum_independent_assessors=2);k2=key(key_id='math-key-2',secret=b'SYNTHETIC_SECOND_KEY_SAME_GROUP_0001',evaluator_id='second')
        rs=signed_reviews(self.request,p)+signed_reviews(self.request,p,k2)
        self.assertCode(self.run_check(p=p,reviews=rs,verifier=ReviewVerifier((key(),k2))),'formula','REVIEW_QUORUM_MISSING','REVIEW_REQUIRED')
    def test_two_independent_groups(self):
        p=replace(self.policy,minimum_independent_assessors=2);k2=key(key_id='math-key-2',secret=b'SYNTHETIC_SECOND_KEY_OTHER_GROUP_001',evaluator_id='second',independence_group='other-group')
        rs=signed_reviews(self.request,p)+signed_reviews(self.request,p,k2)
        self.assertEqual(self.run_check(p=p,reviews=rs,verifier=ReviewVerifier((key(),k2))).status,'CHECKS_PASSED')
    def test_rejection_not_outvoted(self):
        k2=key(key_id='math-key-2',secret=b'SYNTHETIC_SECOND_KEY_OTHER_GROUP_001',evaluator_id='second',independence_group='other-group')
        rs=list(signed_reviews(self.request,self.policy,k2));rs=[sign(replace(a,verdict='REJECTED'),k2) if a.subject_id=='formula-1' else a for a in rs]
        result=self.run_check(reviews=signed_reviews(self.request,self.policy)+tuple(rs),verifier=ReviewVerifier((key(),k2)))
        self.assertCode(result,'formula','REVIEW_REJECTED','BLOCKED')
    def test_shared_secret_independence_rejected(self):
        with self.assertRaises(ContractError):ReviewVerifier((key(),key(key_id='k2',evaluator_id='other',independence_group='other')))
    def test_high_signed_confidence_does_not_override_bad_math(self):
        c=replace(self.request.numericals[0],reported_lo='5000',reported_hi='5000');r=replace(self.request,numericals=(c,))
        rs=tuple(sign(replace(a,confidence_ppm=1000000),key()) for a in signed_reviews(r,self.policy))
        self.assertCode(self.run_check(r,reviews=rs),'numerical','NUMERICAL_OUTSIDE_TOLERANCE','BLOCKED')

class ContractTests(FixtureCase):
    def test_schema_version(self):
        with self.assertRaises(ContractError):replace(self.request,schema_version='2')
    def test_list_not_tuple(self):
        with self.assertRaises(ContractError):replace(self.request,formulas=list(self.request.formulas))
    def test_duplicate_case(self):
        with self.assertRaises(ContractError):replace(self.request,formulas=self.request.formulas*2)
    def test_cross_category_collision(self):
        with self.assertRaises(ContractError):replace(self.request,units=(replace(self.request.units[0],case_id='formula-1'),))
    def test_reserved_subject_collision(self):
        with self.assertRaises(ContractError):replace(self.request,formulas=(replace(self.request.formulas[0],case_id='math-scope'),))
    def test_empty_policy(self):
        with self.assertRaises(ContractError):replace(self.policy,requirements=())
    def test_reversed_bounds(self):
        with self.assertRaises(ContractError):SymbolSpec('x','1',('2','1'))
    def test_invalid_nonzero_symbol(self):
        with self.assertRaises(ContractError):Scope('scope',(SymbolSpec('x','1'),),(parse('y'),))
    def test_duplicate_scope_symbol(self):
        with self.assertRaises(ContractError):Scope('scope',(SymbolSpec('x','1'),SymbolSpec('x','m')))
    def test_scope_symbol_limit(self):
        with self.assertRaises(ContractError):Scope('scope',tuple(SymbolSpec(f'x{i}','1') for i in range(9)))
    def test_empty_claims_rejected(self):
        with self.assertRaises(ContractError):replace(self.request.formulas[0],claim_ids=())
    def test_conditions_same_span_rejected(self):
        with self.assertRaises(ContractError):replace(self.request.formulas[0],condition_claim_ids=('claim-1',))
    def test_step_claim_outside_case(self):
        c=self.request.derivations[0]
        with self.assertRaises(ContractError):replace(c,steps=(replace(c.steps[0],claim_ids=('claim-7',)),))
    def test_empty_derivation(self):
        with self.assertRaises(ContractError):replace(self.request.derivations[0],steps=())
    def test_unknown_step_rule(self):
        with self.assertRaises(ContractError):replace(self.request.derivations[0].steps[0],rule='trust_me')
    def test_negative_tolerance(self):
        with self.assertRaises(ContractError):replace(self.policy.numerical_references[0],abs_tolerance='-1')
    def test_oversized_relative_tolerance(self):
        with self.assertRaises(ContractError):replace(self.policy.numerical_references[0],rel_tolerance='0.02')
    def test_rounding_with_fudge_tolerance_rejected(self):
        with self.assertRaises(ContractError):replace(self.policy.numerical_references[0],mode='rounded_point',abs_tolerance='1')
    def test_uncertain_input_in_point_reference(self):
        ref=self.policy.numerical_references[0]
        with self.assertRaises(ContractError):replace(ref,inputs=(replace(ref.inputs[0],hi='11'),ref.inputs[1]))
    def test_boolean_precision_rejected(self):
        with self.assertRaises(ContractError):replace(self.policy.numerical_references[0],decimal_places=True)
    def test_reference_requires_input_coverage(self):
        with self.assertRaises(ContractError):replace(self.policy.numerical_references[0],inputs=())
    def test_reference_scope_undeclared(self):
        with self.assertRaises(ContractError):replace(self.policy,formula_references=(replace(self.policy.formula_references[0],scope_id='ghost'),))
    def test_requirement_cannot_bind_wrong_scope(self):
        with self.assertRaises(ContractError):replace(self.policy,requirements=(replace(self.policy.requirements[0],scope_id='mechanics'),))
    def test_step_operand_smuggling(self):
        with self.assertRaises(ContractError):replace(self.request.derivations[0].steps[0],rule='rewrite')
