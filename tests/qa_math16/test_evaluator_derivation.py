from math_helpers import *
from bie.qa.math_v2.derivation import check_step
from bie.qa.math_v2.algebra import Proof

class EvaluatorTests(FixtureCase):
    def test_healthy_synthetic(self):self.assertEqual(self.run_check().status,'CHECKS_PASSED')
    def test_missing_inventory_review(self):
        reviews=tuple(a for a in signed_reviews(self.request,self.policy) if a.purpose!='inventory')
        self.assertCode(self.run_check(reviews=reviews),'formula','REVIEW_QUORUM_MISSING','REVIEW_REQUIRED')
    def test_missing_mapping_review(self):
        reviews=tuple(a for a in signed_reviews(self.request,self.policy) if a.subject_id!='formula-1')
        self.assertCode(self.run_check(reviews=reviews),'formula','REVIEW_QUORUM_MISSING')
    def test_unsigned_source_requires_review(self):
        r=evaluate(self.request,self.root,self.policy,as_of=NOW)
        self.assertEqual(r.status,'REVIEW_REQUIRED')
    def test_missing_formula_case(self):self.assertCode(self.run_check(replace(self.request,formulas=())),'formula','REQUIRED_MATH_CASE_MISSING','BLOCKED')
    def test_missing_derivation_case(self):self.assertCode(self.run_check(replace(self.request,derivations=())),'derivation','REQUIRED_MATH_CASE_MISSING')
    def test_missing_numeric_case(self):self.assertCode(self.run_check(replace(self.request,numericals=())),'numerical','REQUIRED_MATH_CASE_MISSING')
    def test_missing_units_case(self):self.assertCode(self.run_check(replace(self.request,units=())),'units','REQUIRED_MATH_CASE_MISSING')
    def test_extra_case(self):
        f=replace(self.request.formulas[0],case_id='unexpected');self.assertCode(self.run_check(replace(self.request,formulas=self.request.formulas+(f,))),'formula','UNEXPECTED_MATH_CASE')
    def test_reference_swap(self):
        f=replace(self.request.formulas[0],reference_id='end');self.assertCode(self.run_check(replace(self.request,formulas=(f,))),'formula','CASE_REQUIREMENT_BINDING_MISMATCH')
    def test_scope_swap(self):
        f=replace(self.request.formulas[0],scope_id='mechanics');self.assertCode(self.run_check(replace(self.request,formulas=(f,))),'formula','CASE_REQUIREMENT_BINDING_MISMATCH')
    def test_wrong_formula(self):
        f=replace(self.request.formulas[0],equation=eq('x','1'));self.assertCode(self.run_check(replace(self.request,formulas=(f,))),'formula','EQUATION_COUNTEREXAMPLE','BLOCKED')
    def test_undeclared_symbol(self):
        f=replace(self.request.formulas[0],equation=eq('z','2'));self.assertCode(self.run_check(replace(self.request,formulas=(f,))),'formula','UNDECLARED_MATH_SYMBOL')
    def test_missing_claim_link(self):
        f=replace(self.request.formulas[0],claim_ids=('absent',));self.assertCode(self.run_check(replace(self.request,formulas=(f,))),'formula','MATH_CLAIM_LINK_MISSING')
    def test_conditions_cannot_be_hidden(self):
        n=replace(self.request.numericals[0],condition_claim_ids=());self.assertCode(self.run_check(replace(self.request,numericals=(n,))),'numerical','DOMAIN_CONDITIONS_NOT_DISCLOSED','BLOCKED')
    def test_condition_assessment_required(self):
        rs=tuple(a for a in signed_reviews(self.request,self.policy) if a.purpose!='disclosure')
        self.assertCode(self.run_check(reviews=rs),'numerical','REVIEW_QUORUM_MISSING','REVIEW_REQUIRED')
    def test_changed_source_rejects(self):
        path=self.root/self.request.source.sources[0].artifact.path;path.write_bytes(path.read_bytes().replace(b'2*x',b'3*x'))
        self.assertCode(self.run_check(),'formula','ARTIFACT_HASH_MISMATCH','BLOCKED')
    def test_missing_output_rejects(self):
        (self.root/self.request.source.outputs[0].artifact.path).unlink();self.assertNotEqual(self.run_check().status,'CHECKS_PASSED')
    def test_stale_result_rejected(self):
        r=self.run_check()
        with self.assertRaises(ContractError):verify_reports(replace(r,witnesses=()),self.request,self.root,self.policy,as_of=NOW,**options(self.request,self.policy))
    def test_valid_result_recomputed(self):
        r=self.run_check();self.assertEqual(verify_reports(r,self.request,self.root,self.policy,as_of=NOW,**options(self.request,self.policy)),r)
    def test_deterministic_run(self):self.assertEqual(self.run_check().to_dict(),self.run_check().to_dict())
    def test_review_order_does_not_change_digest(self):
        rs=signed_reviews(self.request,self.policy);self.assertEqual(self.run_check(reviews=rs),self.run_check(reviews=tuple(reversed(rs))))
    def test_no_product_acceptance_property(self):self.assertFalse(self.run_check().product_accepted)
    def test_unit_conversion_bad_value(self):
        c=self.request.units[0];u=replace(c,conversions=(replace(c.conversions[0],reported_lo='100',reported_hi='100'),))
        self.assertCode(self.run_check(replace(self.request,units=(u,))),'units','UNIT_CONVERSION_VALUE_MISMATCH','BLOCKED')
    def test_unit_equation_mismatch(self):
        c=replace(self.request.units[0],equation=eq('d','t'));self.assertCode(self.run_check(replace(self.request,units=(c,))),'units','EQUATION_DIMENSION_MISMATCH','BLOCKED')
    def test_nonempty_scope_witness(self):
        s=replace(self.policy.scopes[0],symbols=(SymbolSpec('x','1',('0','0')),),nonzero=(parse('x'),));p=replace(self.policy,scopes=(s,self.policy.scopes[1]));r=self.run_check(p=p)
        self.assertCode(r,'formula','SCOPE_NONEMPTY_WITNESS_MISSING')
    def test_empty_category_is_not_implicit_pass(self):
        p=replace(self.policy,requirements=tuple(x for x in self.policy.requirements if x.kind!='units'))
        r=replace(self.request,units=());self.assertCode(self.run_check(r,p),'units','CATEGORY_SCOPE_NOT_EVALUATED','REVIEW_REQUIRED')
    def test_domain_hole_not_algebraically_erased(self):
        f=replace(self.request.formulas[0],equation=eq('(x*x)/x','2'))
        self.assertCode(self.run_check(replace(self.request,formulas=(f,))),'formula','NONZERO_DOMAIN_UNPROVEN','REVIEW_REQUIRED')
    def test_math_witness_binds_candidate_and_policy(self):
        r=self.run_check();self.assertEqual(r.formula.request_digest,self.request.content_digest);self.assertEqual(r.formula.policy_digest,self.policy.content_digest)
    def test_numeric_failure_propagates(self):
        n=replace(self.request.numericals[0],reported_lo='6',reported_hi='6');r=self.run_check(replace(self.request,numericals=(n,)))
        self.assertCode(r,'numerical','NUMERICAL_OUTSIDE_TOLERANCE','BLOCKED');self.assertEqual(r.status,'BLOCKED')

class DerivationTests(FixtureCase):
    def step(self,**changes):return replace(self.request.derivations[0].steps[0],**changes)
    def prove(self,step,scope=None):return check_step(step,scope or self.policy.scopes[0])
    def test_subtract_both(self):self.assertEqual(self.prove(self.step()).status,'PROVED')
    def test_add_both(self):self.assertEqual(self.prove(self.step(before=eq('x','2'),after=eq('x+2','4'),rule='add_both')).status,'PROVED')
    def test_multiply_both(self):self.assertEqual(self.prove(self.step(before=eq('x','2'),after=eq('2*x','4'),rule='multiply_both')).status,'PROVED')
    def test_divide_both(self):self.assertEqual(self.prove(self.request.derivations[0].steps[1]).status,'PROVED')
    def test_one_side_operation_not_enough(self):self.assertEqual(self.prove(self.step(after=eq('2*x','6'))).code,'STEP_OPERATION_MISMATCH')
    def test_swap(self):self.assertEqual(self.prove(self.step(after=eq('6','2*x+2'),rule='swap',operand=num(0))).status,'PROVED')
    def test_invalid_swap(self):self.assertEqual(self.prove(self.step(after=eq('6','2*x'),rule='swap',operand=num(0))).status,'DISPROVED')
    def test_rewrite(self):self.assertEqual(self.prove(self.step(after=eq('x+1','3'),rule='rewrite',operand=num(0))).status,'PROVED')
    def test_multiply_zero_not_equivalence(self):self.assertEqual(self.prove(self.step(before=eq('x','2'),after=eq('0','0'),rule='multiply_both',operand=num(0))).code,'REVERSIBILITY_NONZERO_FACTOR_UNPROVEN')
    def test_divide_symbol_requires_nonzero(self):self.assertNotEqual(self.prove(self.step(before=eq('x*x','2*x'),after=eq('x','2'),rule='divide_both',operand=parse('x'))).status,'PROVED')
    def test_divide_symbol_under_reviewed_nonzero(self):
        s=replace(self.policy.scopes[0],nonzero=(parse('x'),));step=self.step(before=eq('x*x','2*x'),after=eq('x','2'),rule='divide_both',operand=parse('x'))
        self.assertEqual(self.prove(step,s).status,'PROVED')
    def test_square_without_branch(self):
        step=self.step(before=eq('x','1'),after=eq('x^2','1'),rule='square_both',operand=num(0));self.assertNotEqual(self.prove(step).status,'PROVED')
    def test_square_with_positive_branch(self):
        s=replace(self.policy.scopes[0],symbols=(SymbolSpec('x','1',('0','2')),));step=self.step(before=eq('x','1'),after=eq('x^2','1'),rule='square_both',operand=num(0))
        self.assertEqual(self.prove(step,s).status,'PROVED')
    def test_square_with_negative_branch(self):
        s=replace(self.policy.scopes[0],symbols=(SymbolSpec('x','1',('-2','0')),));step=self.step(before=eq('x','-1'),after=eq('x^2','1'),rule='square_both',operand=num(0))
        self.assertEqual(self.prove(step,s).status,'PROVED')
    def test_square_mixed_sign_branch(self):
        s=replace(self.policy.scopes[0],symbols=(SymbolSpec('x','1',('-2','2')),));step=self.step(before=eq('x','1'),after=eq('x^2','1'),rule='square_both',operand=num(0))
        self.assertEqual(self.prove(step,s).code,'SQUARING_BRANCH_NOT_PROVEN_INJECTIVE')
    def test_calculus_not_fake_equivalence(self):self.assertEqual(self.prove(self.step(rule='differentiate',operand=num(0))).code,'UNSUPPORTED_DERIVATION_RULE')
    def test_substitution_requires_future_contract(self):self.assertEqual(self.prove(self.step(rule='substitute',operand=num(0))).code,'UNSUPPORTED_DERIVATION_RULE')
    def test_chain_break(self):
        c=self.request.derivations[0];step=replace(c.steps[1],before=eq('x','2'),after=eq('x','2'),rule='rewrite',operand=num(0));c=replace(c,steps=(c.steps[0],step))
        self.assertCode(self.run_check(replace(self.request,derivations=(c,))),'derivation','DERIVATION_CHAIN_DISCONTINUITY','BLOCKED')
    def test_missing_explanatory_step(self):
        c=self.request.derivations[0];c=replace(c,steps=(replace(c.steps[0],after=eq('x','2'),rule='rewrite',operand=num(0)),))
        self.assertCode(self.run_check(replace(self.request,derivations=(c,))),'derivation','DERIVATION_MINIMUM_STEPS_MISSING','BLOCKED')
    def test_terminal_target_mismatch(self):
        c=self.request.derivations[0];c=replace(c,end_reference_id='start')
        self.assertCode(self.run_check(replace(self.request,derivations=(c,))),'derivation','CASE_REQUIREMENT_BINDING_MISMATCH')
    def test_unreviewed_step_not_pass(self):
        rs=tuple(a for a in signed_reviews(self.request,self.policy) if a.subject_id!='step-1')
        self.assertCode(self.run_check(reviews=rs),'derivation','REVIEW_QUORUM_MISSING','REVIEW_REQUIRED')
