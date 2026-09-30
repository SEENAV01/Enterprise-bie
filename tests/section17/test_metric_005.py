from batch003_helpers import MetricBase,attach_metric_fixtures
from bie.evaluation.benchmarks.metrics.mathematics import mul
from fractions import Fraction
@attach_metric_fixtures
class METRIC005Tests(MetricBase):
    task='BIE-EVAL-METRIC-005'
    def test_absolute_tolerance_uses_canonical_base_unit(self):
        r,c,a=self.example();r['payload']['checks'][0]['absolute_tolerance']='1/100';c['checks'][0]['value']={'value':101,'unit':'cm'};self.assertEqual('PASS',self.measure(r,c,a)['outcome']);c['checks'][0]['value']['value']='10101/100';self.assertEqual('FAIL',self.measure(r,c,a)['outcome'])
    def test_relative_tolerance_at_limit(self):
        r,c,a=self.example();r['payload']['checks'][0]['relative_tolerance']='1/100';c['checks'][0]['value']={'value':'101/100','unit':'m'};self.assertEqual('PASS',self.measure(r,c,a)['outcome'])
    def test_inflated_tolerance_rejected(self):
        r,c,a=self.example();r['payload']['checks'][0]['relative_tolerance']='1/10';self.reject(r,c,a,code='TOLERANCE_OUT_OF_PROFILE')
    def test_symbolic_tolerance_not_allowed(self):
        r,c,a=self.example();r['payload']['checks'][1]['absolute_tolerance']='1/100';self.reject(r,c,a,code='EXACT_ALGEBRA_TOLERANCE_REQUIRED')
    def test_celsius_kelvin_offset(self):
        r,c,a=self.example();r['payload']['checks'][0]['expected']={'value':0,'unit':'degC'};c['checks'][0]['value']={'value':'5463/20','unit':'K'};self.assertEqual('PASS',self.measure(r,c,a)['outcome'])
    def test_negative_kelvin_blocked(self):
        r,c,a=self.example();c['checks'][0]['value']={'value':-1,'unit':'K'};self.reject(r,c,a,code='BELOW_ABSOLUTE_ZERO')
    def test_candidate_extra_domain_hole_fails(self):
        r,c,a=self.example();c['checks'][2]['value']['excluded_values'].append(2);self.assertEqual('1/2',self.measure(r,c,a)['score_exact'])
    def test_denominator_root_requires_exclusion(self):
        r,c,a=self.example();c['checks'][2]['value']['denominator_roots']=[2];self.reject(r,c,a,code='DENOMINATOR_ROOT_NOT_EXCLUDED')
    def test_duplicate_domain_hole_rejected(self):
        r,c,a=self.example();c['checks'][2]['value']['excluded_values']=[1,1];self.reject(r,c,a,code='DUPLICATE_DOMAIN_EXCLUSION')
    def test_polynomial_product_coefficient_order(self):
        self.assertEqual([Fraction(-1),Fraction(0),Fraction(1)],mul([Fraction(1),Fraction(1)],[Fraction(-1),Fraction(1)]))
    def test_expression_string_never_evaluated(self):
        r,c,a=self.example();c['checks'][1]['value']='__import__("os").system("false")';self.reject(r,c,a)
    def test_polynomial_degree_bounded(self):
        r,c,a=self.example();c['checks'][1]['value']=[1]*10;self.reject(r,c,a,code='COLLECTION_SIZE_OR_TYPE')
    def test_zero_polynomial_normalizes_trailing_zeros(self):
        r,c,a=self.example();r['payload']['checks'][1]['expected']=[0];c['checks'][1]['value']=[0,0,0];self.assertEqual('PASS',self.measure(r,c,a)['outcome'])
    def test_numeric_wrong_value_cannot_be_masked_by_unit_label(self):
        r,c,a=self.example();c['checks'][0]['value']={'value':100,'unit':'m'};self.assertEqual('3/4',self.measure(r,c,a)['score_exact'])
