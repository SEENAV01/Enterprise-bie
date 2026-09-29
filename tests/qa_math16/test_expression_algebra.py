import unittest
from fractions import Fraction as Q
from bie.qa.math_v2.expression import *
from bie.qa.math_v2.algebra import *
from bie.qa.math_v2.units import *
from bie.qa.math_v2.models import Equation

class ParserTests(unittest.TestCase):
    def test_decimal_is_exact(self):self.assertEqual(rational('0.1')+rational('0.2'),rational('0.3'))
    def test_scientific_literal(self):self.assertEqual(parse('1.25e-2'),num('1/80'))
    def test_precedence(self):self.assertEqual(interval(parse('2+3*4'),{}).lo,Q(14))
    def test_left_associative_subtraction(self):self.assertEqual(interval(parse('10-3-2'),{}).lo,Q(5))
    def test_chained_power_requires_literal_exponent(self):
        with self.assertRaises(ContractError):parse('2^2^3')
    def test_unary_power_precedence(self):self.assertEqual(interval(parse('-2^2'),{}).lo,Q(-4))
    def test_negative_power(self):self.assertEqual(interval(parse('2^-2'),{}).lo,Q(1,4))
    def test_function_nodes(self):self.assertEqual(parse('sqrt(x)').op,'sqrt')
    def test_symbol_inventory(self):self.assertEqual(parse('x*y+x').symbols,{'x','y'})
    def test_frozen_ast(self):
        with self.assertRaises(Exception):parse('x').value='y'
    def test_canonical_numeric_nodes(self):
        with self.assertRaises(ContractError):Expr('num','0.50')
    def test_bool_not_number(self):
        with self.assertRaises(ContractError):num(True)
    def test_float_not_number(self):
        with self.assertRaises(ContractError):num(0.1)
    def test_invalid_arity(self):
        with self.assertRaises(ContractError):Expr('add','',(num(1),))
    def test_fraction_constructor(self):self.assertEqual(rational('2/4'),Q(1,2))
    def test_resource_power(self):
        with self.assertRaises(ContractError):parse('x^9')
    def test_symbolic_power(self):
        with self.assertRaises(ContractError):parse('x^y')
    def test_fractional_power(self):
        with self.assertRaises(ContractError):parse('x^(1/2)')
    def test_depth_limit(self):
        with self.assertRaises(ContractError):parse('('*30+'x'+')'*30)
    def test_token_limit(self):
        with self.assertRaises(ContractError):parse('+'.join(['x']*160))
    def test_long_number(self):
        with self.assertRaises(ContractError):parse('9'*161)
    def test_huge_exponent(self):
        with self.assertRaises(ContractError):parse('1e9999999')
    def test_huge_fraction(self):
        with self.assertRaises(ContractError):rational('1/'+('9'*160))
    def test_unexpected_operator_value(self):
        with self.assertRaises(ContractError):Expr('add','override',(num(1),num(2)))

REJECT_TEXTS={
 'import':'__import__("os")','attribute':'x.real','index':'x[0]','lambda':'lambda x: x','list':'[1,2]',
 'dict':'{"x":1}','implicit_mul':'2x','latex':r'\frac{1}{2}','unicode_minus':'x−1','unicode_symbol':'α+1',
 'comparison':'x==1','assignment':'x=1','trailing':'x y','empty':' ','parenthesis':'(x+1','call_arity':'sqrt(x,y)',
 'unknown_call':'open(x)','floor_div':'x//2','semicolon':'x;1','unary_only':'-','trailing_operator':'x+',
 'nan':'NaN(1)','hex':'0xff','underscore_numeric':'1_000','modulo':'x%2','nul':'x\x00',
}
for name,text in REJECT_TEXTS.items():
    def make(text):
        def check(self):
            with self.assertRaises(ContractError):parse(text)
        return check
    setattr(ParserTests,'test_reject_'+name,make(text))

class AlgebraTests(unittest.TestCase):
    def test_binomial_identity(self):self.assertTrue(equal_expressions(parse('(x+1)^2'),parse('x^2+2*x+1')))
    def test_distributive_property(self):
        for a in range(-4,5):
            with self.subTest(a=a):self.assertTrue(equal_expressions(parse(f'{a}*(x+y)'),parse(f'{a}*x+{a}*y')))
    def test_polynomial_difference(self):self.assertFalse(equal_expressions(parse('x^2'),parse('x')))
    def test_rearrangement_certificate(self):self.assertEqual(compare_equations(parse('2*x+2'),num(6),parse('x'),num(2),{}).status,'PROVED')
    def test_counterexample(self):
        p=compare_equations(parse('x^2'),num(1),parse('x'),num(1),{})
        self.assertEqual(p.status,'DISPROVED');self.assertIn(('x','-1'),p.witness)
    def test_no_proof_from_finite_samples(self):self.assertEqual(compare_equations(parse('x^3'),num(0),parse('x'),num(0),{}).status,'UNKNOWN')
    def test_identical_but_undefined_formula_unknown(self):self.assertEqual(compare_equations(parse('x/x'),num(1),parse('x/x'),num(1),{}).status,'UNKNOWN')
    def test_denominator_condition_retained(self):self.assertTrue(domain_issues(parse('0*(1/x)'),{}))
    def test_cancelled_hole(self):self.assertTrue(domain_issues(parse('(x^2-1)/(x-1)'),{}))
    def test_nonzero_assumption(self):self.assertFalse(domain_issues(parse('x/x'),{},(parse('x'),)))
    def test_nonzero_bound(self):self.assertFalse(domain_issues(parse('1/x'),{'x':Interval(Q(1),Q(2))}))
    def test_negative_nonzero_bound(self):self.assertTrue(known_nonzero(parse('x'),{'x':Interval(Q(-3),Q(-1))}))
    def test_nonzero_product(self):self.assertTrue(known_nonzero(parse('x*y'),{},(parse('x'),parse('y'))))
    def test_zero_nonzero_not_inferred(self):self.assertFalse(known_nonzero(num(0),{}))
    def test_identically_zero_divisor_rejected(self):
        with self.assertRaises(ContractError):rational_polynomial(parse('1/(x-x)'))
    def test_zero_power_rejected(self):
        with self.assertRaises(ContractError):interval(parse('0^0'),{})
    def test_symbolic_function_unknown(self):self.assertEqual(compare_equations(parse('sin(x)'),num(0),parse('sin(x)'),num(0),{}).status,'UNKNOWN')
    def test_abs_not_assumed_x(self):
        with self.assertRaises(ContractError):equal_expressions(parse('abs(x)'),parse('x'))
    def test_polynomial_expansion_budget(self):
        with self.assertRaises(ContractError):rational_polynomial(parse('(a+b+c+d)^8'))
    def test_inconsistent_equation_not_accepted(self):self.assertEqual(compare_equations(num(1),num(0),num(2),num(0),{}).status,'UNKNOWN')
    def test_point_enumeration_is_bounded(self):self.assertLessEqual(len(list(sample_points(set('abcdef'),{},limit=17))),17)
    def test_empty_constraint_scope(self):self.assertEqual(list(sample_points({'x'},{'x':Interval(Q(0),Q(0))},(parse('x'),))),[])
    def test_interval_negative_multiplication(self):self.assertEqual(interval(parse('x*y'),{'x':Interval(Q(-2),Q(3)),'y':Interval(Q(-4),Q(5))}).text(),('-12','15'))
    def test_interval_even_power_zero(self):self.assertEqual(interval(parse('x^2'),{'x':Interval(Q(-2),Q(3))}).text(),('0','9'))
    def test_interval_negative_power(self):self.assertEqual(interval(parse('x^-2'),{'x':Interval(Q(2),Q(4))}).text(),('1/16','1/4'))
    def test_division_straddling_zero(self):
        with self.assertRaises(ContractError):interval(parse('1/x'),{'x':Interval(Q(-1),Q(1))})
    def test_sqrt_enclosure(self):
        x=interval(parse('sqrt(2)'),{});self.assertLessEqual(x.lo*x.lo,2);self.assertGreaterEqual(x.hi*x.hi,2)
    def test_perfect_sqrt(self):self.assertEqual(interval(parse('sqrt(4/9)'),{}).text(),('2/3','2/3'))
    def test_interval_endpoint_properties(self):
        for lo in range(-3,3):
            for hi in range(lo,4):
                v=Interval(Q(lo),Q(hi))
                for op in ('x^2','x^3','abs(x)','-x','x*x+2*x'):
                    w=interval(parse(op),{'x':v})
                    for x in (v.lo,(v.lo+v.hi)/2,v.hi):
                        with self.subTest(lo=lo,hi=hi,op=op,x=str(x)):
                            p=interval(parse(op),{'x':Interval(x,x)});self.assertLessEqual(w.lo,p.lo);self.assertGreaterEqual(w.hi,p.hi)
