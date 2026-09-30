import math
from domain_helpers import DomainBase
from bie.evaluation.benchmarks.domains.calculus import solve

class CalculusTests(DomainBase):
    def test_authored_reference_pack(self):self.replay_pack('BIE-EVAL-MATH-002')
    def test_constant_derivative_zero(self):self.assertEqual(['0'],solve(dict(op='differentiate_polynomial',coefficients=[3],order=1))['coefficients'])
    def test_order_zero_is_identity(self):self.assertEqual(['2','3'],solve(dict(op='differentiate_polynomial',coefficients=[2,3,0],order=0))['coefficients'])
    def test_derivative_order_higher_than_degree(self):self.assertEqual(['0'],solve(dict(op='differentiate_polynomial',coefficients=[2,3],order=8))['coefficients'])
    def test_derivative_fraction_coefficients(self):self.assertEqual(['1/3','1/2'],solve(dict(op='differentiate_polynomial',coefficients=[0,'1/3','1/4'],order=1))['coefficients'])
    def test_antiderivative_requires_arbitrary_constant(self):
        r=solve(dict(op='antiderivative_polynomial',coefficients=[0,2]));self.assertEqual('C',r['arbitrary_constant']);self.assertEqual(['0','0','1'],r['particular_coefficients'])
    def test_fundamental_theorem_polynomial(self):
        p=[2,3,4];anti=solve(dict(op='antiderivative_polynomial',coefficients=p))['particular_coefficients'];self.assertEqual([str(c) for c in p],solve(dict(op='differentiate_polynomial',coefficients=anti,order=1))['coefficients'])
    def test_integral_zero_interval(self):self.assertEqual('0',solve(dict(op='definite_integral_polynomial',coefficients=[3,4,5],lower=2,upper=2))['exact'])
    def test_integral_orientation(self):
        a=solve(dict(op='definite_integral_polynomial',coefficients=[0,2],lower=0,upper=3));b=solve(dict(op='definite_integral_polynomial',coefficients=[0,2],lower=3,upper=0));self.assertEqual(a['value'],-b['value'])
    def test_odd_integrand_symmetric_interval(self):self.assertEqual('0',solve(dict(op='definite_integral_polynomial',coefficients=[0,0,0,1],lower=-2,upper=2))['exact'])
    def test_tangent_point_independent(self):self.assertEqual({'slope_exact':'6','intercept_exact':'-4'},solve(dict(op='tangent_polynomial',coefficients=[0,2,1],x=2)))
    def test_cusp_not_derivative_zero(self):self.code('NONDIFFERENTIABLE_AT_POINT',solve,dict(op='derivative_absolute_value',x=0))
    def test_abs_positive_derivative(self):self.assertEqual(1,solve(dict(op='derivative_absolute_value',x='1/8'))['derivative'])
    def test_reciprocal_negative_interval(self):self.assertAlmostEqual(-math.log(2),solve(dict(op='definite_integral_reciprocal',lower=-2,upper=-1))['value'])
    def test_principal_value_not_improper_integral(self):self.code('INTEGRATION_INTERVAL_CROSSES_SINGULARITY',solve,dict(op='definite_integral_reciprocal',lower=-1,upper=1))
    def test_singular_endpoint_rejected(self):self.code('INTEGRATION_INTERVAL_CROSSES_SINGULARITY',solve,dict(op='definite_integral_reciprocal',lower=0,upper=1))
    def test_order_boolean_rejected(self):self.code('INVALID_INTEGER',solve,dict(op='differentiate_polynomial',coefficients=[1],order=True))
    def test_negative_derivative_order_rejected(self):self.code('INVALID_INTEGER',solve,dict(op='differentiate_polynomial',coefficients=[1],order=-1))
    def test_missing_arbitrary_constant_seed_rejected(self):self.mutant('BIE-EVAL-MATH-002',2,['values','arbitrary_constant'],'')
    def test_wrong_integral_orientation_seed_rejected(self):self.mutant('BIE-EVAL-MATH-002',4,['values','exact'],'8')
