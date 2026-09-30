from domain_helpers import DomainBase
from bie.evaluation.benchmarks.domains.functions import solve

class FunctionsTests(DomainBase):
    def test_authored_reference_pack(self):self.replay_pack('BIE-EVAL-MATH-001')
    def test_exact_rational_polynomial(self):self.assertEqual({'exact':'1/3','value':1/3},solve(dict(op='polynomial_value',coefficients=['1/6','1/3'],x='1/2')))
    def test_zero_polynomial(self):self.assertEqual('0',solve(dict(op='polynomial_value',coefficients=[0],x=999))['exact'])
    def test_negative_argument(self):self.assertEqual('9',solve(dict(op='polynomial_value',coefficients=[1,2,3],x=-2))['exact'])
    def test_composition_order_matters(self):
        a=solve(dict(op='composition_value',outer=[0,0,1],inner=[1,1],x=2));b=solve(dict(op='composition_value',outer=[1,1],inner=[0,0,1],x=2));self.assertEqual('9',a['exact']);self.assertEqual('5',b['exact'])
    def test_inverse_roundtrip(self):
        r=solve(dict(op='inverse_affine_value',a=3,b=-2,y=13));self.assertEqual('5',r['exact'])
    def test_noninvertible_constant(self):self.code('NONINVERTIBLE_FUNCTION',solve,dict(op='inverse_affine_value',a=0,b=2,y=2))
    def test_uncancelled_domain_hole(self):self.code('OUTSIDE_ORIGINAL_DOMAIN',solve,dict(op='rational_value',numerator=[-1,0,1],denominator=[-1,1],x=1))
    def test_identically_zero_denominator(self):self.code('OUTSIDE_ORIGINAL_DOMAIN',solve,dict(op='rational_value',numerator=[1],denominator=[0],x=17))
    def test_consistent_duplicate_pair_is_function(self):
        r=solve(dict(op='finite_relation',pairs=[[1,2],[1,2],[2,3]]));self.assertTrue(r['is_function']);self.assertEqual(2,r['domain_cardinality'])
    def test_multiple_outputs_not_function(self):
        r=solve(dict(op='finite_relation',pairs=[[1,2],[1,3]]));self.assertFalse(r['is_function']);self.assertEqual(['1'],r['conflicting_inputs'])
    def test_many_to_one_not_injective(self):self.assertFalse(solve(dict(op='finite_relation',pairs=[[1,3],[2,3]]))['is_injective'])
    def test_exact_rational_input_identity(self):
        r=solve(dict(op='finite_relation',pairs=[['1/2',2],['2/4',3]]));self.assertFalse(r['is_function'])
    def test_boolean_coefficient_rejected(self):self.code('INVALID_RATIONAL',solve,dict(op='polynomial_value',coefficients=[True],x=1))
    def test_degree_limit_rejected(self):self.code('POLYNOMIAL_DEGREE_LIMIT',solve,dict(op='polynomial_value',coefficients=[1]*34,x=1))
    def test_python_expression_not_executed(self):self.code('INVALID_RATIONAL',solve,dict(op='polynomial_value',coefficients=['__import__("os").system("echo unsafe")'],x=1))
    def test_invalid_fraction_zero_denominator(self):self.code('INVALID_RATIONAL',solve,dict(op='polynomial_value',coefficients=['1/0'],x=1))
    def test_unsupported_transcendental_not_fake_symbolic(self):self.code('UNSUPPORTED_OPERATION',solve,{'op':'solve_arbitrary_transcendental'})
    def test_cancelled_hole_wrong_success_rejected(self):self.mutant('BIE-EVAL-MATH-001',2,['status'],'OK')
    def test_wrong_composition_seed_rejected(self):self.mutant('BIE-EVAL-MATH-001',3,['values','exact'],'25')
