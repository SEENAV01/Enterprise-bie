from math_helpers import *
from fractions import Fraction as Q
from bie.qa.math_v2.algebra import Interval,interval
from bie.qa.math_v2.units import *
from bie.qa.math_v2.numerical import check_numeric,rounded_text

class UnitTests(unittest.TestCase):
    def test_force_dimension(self):self.assertEqual(unit('N').dimensions,unit('kg*m/s^2').dimensions)
    def test_force_energy_differ(self):self.assertNotEqual(unit('N').dimensions,unit('J').dimensions)
    def test_minutes(self):self.assertEqual(convert(Interval(Q(2),Q(2)),'min','s').text(),('120','120'))
    def test_cm_to_m(self):self.assertEqual(convert(Interval(Q(100),Q(100)),'cm','m').text(),('1','1'))
    def test_kmh_to_ms(self):self.assertEqual(convert(Interval(Q(36),Q(36)),'km/h','m/s').text(),('10','10'))
    def test_liter(self):self.assertEqual(convert(Interval(Q(1),Q(1)),'L','m^3').text(),('1/1000','1/1000'))
    def test_celsius_absolute(self):self.assertEqual(convert(Interval(Q(0),Q(0)),'degC','K').text(),('5463/20','5463/20'))
    def test_fahrenheit_freezing(self):self.assertEqual(convert(Interval(Q(32),Q(32)),'degF','degC').text(),('0','0'))
    def test_fahrenheit_boiling(self):self.assertEqual(convert(Interval(Q(212),Q(212)),'degF','degC').text(),('100','100'))
    def test_temperature_difference(self):self.assertEqual(convert(Interval(Q(9),Q(9)),'delta_degF','delta_K').text(),('5','5'))
    def test_absolute_vs_difference_rejected(self):
        with self.assertRaises(ContractError):convert(Interval(Q(1),Q(1)),'degC','delta_K')
    def test_temperature_below_zero(self):
        with self.assertRaises(ContractError):convert(Interval(Q(-274),Q(-274)),'degC','K')
    def test_offset_units_not_multiplied(self):
        with self.assertRaises(ContractError):unit('degC*m')
    def test_angle_not_count(self):
        with self.assertRaises(ContractError):convert(Interval(Q(1),Q(1)),'rad','1')
    def test_unknown_unit(self):
        with self.assertRaises(ContractError):unit('furlong')
    def test_case_sensitive(self):
        with self.assertRaises(ContractError):unit('n')
    def test_addition_mismatch(self):
        with self.assertRaises(ContractError):dimension(parse('x+t'),{'x':'m','t':'s'})
    def test_matching_dimensions_not_formula_proof(self):self.assertTrue(same_dimensions(parse('d'),parse('2*v*t'),{'d':'m','v':'m/s','t':'s'}))
    def test_dimensional_zero(self):self.assertTrue(same_dimensions(parse('x'),num(0),{'x':'m'}))
    def test_dimensional_function_input(self):
        with self.assertRaises(ContractError):dimension(parse('log(x)'),{'x':'m'})
    def test_sqrt_dimension(self):self.assertEqual(dimension(parse('sqrt(x)'),{'x':'m^2'}),unit('m').dimensions)
    def test_fractional_dimensions_review(self):
        with self.assertRaises(ContractError):dimension(parse('sqrt(x)'),{'x':'m'})
    def test_affine_formula_requires_normalization(self):
        with self.assertRaises(ContractError):dimension(parse('T'),{'T':'degC'})
    def test_unit_registry_immutable(self):
        with self.assertRaises(TypeError):UNITS['bogus']=unit('m')
    def test_roundtrip_conversions(self):
        for a,b in [('m','cm'),('s','h'),('km/h','m/s'),('degC','degF'),('delta_K','delta_degF')]:
            for lo,hi in [(0,1),(10,30),(32,212)]:
                with self.subTest(a=a,b=b,lo=lo):
                    v=Interval(Q(lo),Q(hi));self.assertEqual(convert(convert(v,a,b),b,a),v)

class NumericTests(FixtureCase):
    def numeric(self,c=None,ref=None,scope=None):return check_numeric(c or self.request.numericals[0],ref or self.policy.numerical_references[0],scope or self.policy.scopes[1])
    def test_speed_exact(self):self.assertEqual(self.numeric()[0].status,'PROVED')
    def test_incorrect_result(self):self.assertEqual(self.numeric(replace(self.request.numericals[0],reported_lo='6',reported_hi='6'))[0].code,'NUMERICAL_OUTSIDE_TOLERANCE')
    def test_no_float_cancellation(self):
        c=self.request.numericals[0];s=Scope('mechanics',());ref=NumericalReference('speed','mechanics',parse('0.1+0.2'),(),'1');c=replace(c,expression=ref.expression,inputs=(),reported_lo='0.3',reported_hi='0.3',output_unit='1')
        self.assertEqual(self.numeric(c,ref,s)[0].status,'PROVED')
    def test_input_value_tampered(self):
        c=self.request.numericals[0];c=replace(c,inputs=(replace(c.inputs[0],lo='12',hi='12'),c.inputs[1]))
        self.assertEqual(self.numeric(c)[0].code,'NUMERICAL_INPUT_VALUE_MISMATCH')
    def test_input_units_converted(self):
        c=self.request.numericals[0];c=replace(c,inputs=(replace(c.inputs[0],lo='1000',hi='1000',unit='cm'),c.inputs[1]))
        self.assertEqual(self.numeric(c)[0].status,'PROVED')
    def test_input_unit_dimension_mismatch(self):
        c=self.request.numericals[0];c=replace(c,inputs=(replace(c.inputs[0],unit='s'),c.inputs[1]))
        self.assertEqual(self.numeric(c)[0].code,'NUMERICAL_INPUT_UNIT_MISMATCH')
    def test_output_unit_swap_rejected(self):self.assertEqual(self.numeric(replace(self.request.numericals[0],output_unit='km/h'))[0].code,'NUMERICAL_OUTPUT_UNIT_MISMATCH')
    def test_missing_input(self):self.assertEqual(self.numeric(replace(self.request.numericals[0],inputs=()))[0].code,'NUMERICAL_BINDING_INVENTORY_MISMATCH')
    def test_wrong_expression_not_passed(self):self.assertNotEqual(self.numeric(replace(self.request.numericals[0],expression=parse('d*t')))[0].status,'PROVED')
    def test_relative_tolerance(self):
        c=replace(self.request.numericals[0],reported_lo='5.005',reported_hi='5.005');ref=replace(self.policy.numerical_references[0],rel_tolerance='0.001')
        self.assertEqual(self.numeric(c,ref)[0].status,'PROVED')
    def test_relative_tolerance_outside(self):
        c=replace(self.request.numericals[0],reported_lo='5.006',reported_hi='5.006');ref=replace(self.policy.numerical_references[0],rel_tolerance='0.001')
        self.assertEqual(self.numeric(c,ref)[0].status,'DISPROVED')
    def test_point_cannot_be_interval(self):self.assertEqual(self.numeric(replace(self.request.numericals[0],reported_lo='4',reported_hi='6'))[0].code,'POINT_REPORT_IS_INTERVAL')
    def test_domain_violation(self):
        inputs=(Binding('d','101','101','m'),Binding('t','2','2','s'));ref=replace(self.policy.numerical_references[0],inputs=inputs);c=replace(self.request.numericals[0],inputs=inputs)
        self.assertEqual(self.numeric(c,ref)[0].code,'NUMERICAL_INPUT_OUTSIDE_DOMAIN')
    def test_reference_hole_not_cancelled(self):
        scope=Scope('mechanics',(SymbolSpec('x','1'),));inputs=(Binding('x','0','0','1'),)
        ref=NumericalReference('speed','mechanics',parse('(x*x)/x'),inputs,'1');c=replace(self.request.numericals[0],expression=parse('x'),inputs=inputs,reported_lo='0',reported_hi='0',output_unit='1')
        self.assertNotEqual(self.numeric(c,ref,scope)[0].status,'PROVED')
    def test_candidate_hole_not_cancelled(self):
        scope=Scope('mechanics',(SymbolSpec('x','1'),));inputs=(Binding('x','0','0','1'),)
        ref=NumericalReference('speed','mechanics',parse('x'),inputs,'1');c=replace(self.request.numericals[0],expression=parse('(x*x)/x'),inputs=inputs,reported_lo='0',reported_hi='0',output_unit='1')
        self.assertNotEqual(self.numeric(c,ref,scope)[0].status,'PROVED')
    def test_half_even(self):
        for value,expected in [('2.345','2.34'),('2.355','2.36'),('-2.345','-2.34'),('-2.355','-2.36'),('-0.001','0.00')]:
            with self.subTest(value=value):self.assertEqual(rounded_text(Q(value),2),expected)
    def test_rounded_decimal_lexeme(self):
        ref=replace(self.policy.numerical_references[0],mode='rounded_point',decimal_places=2);c=replace(self.request.numericals[0],reported_lo='5.00',reported_hi='5.00')
        self.assertEqual(self.numeric(c,ref)[0].status,'PROVED')
    def test_false_precision_rejected(self):
        ref=replace(self.policy.numerical_references[0],mode='rounded_point',decimal_places=2)
        self.assertEqual(self.numeric(self.request.numericals[0],ref)[0].code,'ROUNDING_OR_PRECISION_MISMATCH')
    def test_sqrt_interval_supported(self):
        scope=Scope('mechanics',());ref=NumericalReference('speed','mechanics',parse('sqrt(2)'),(),'1',mode='interval',max_interval_width='1/1000')
        c=replace(self.request.numericals[0],expression=ref.expression,inputs=(),reported_lo='1.414',reported_hi='1.415',output_unit='1')
        self.assertEqual(self.numeric(c,ref,scope)[0].status,'PROVED')
    def test_interval_width_cannot_game(self):
        scope=Scope('mechanics',());ref=NumericalReference('speed','mechanics',num(2),(),'1',mode='interval',max_interval_width='1')
        c=replace(self.request.numericals[0],expression=num(2),inputs=(),reported_lo='-1000',reported_hi='1000',output_unit='1')
        self.assertEqual(self.numeric(c,ref,scope)[0].code,'NUMERICAL_ENCLOSURE_TOO_WIDE')
    def test_uncertain_input_does_not_earn_point_precision(self):
        inputs=(Binding('d','9','11','m'),Binding('t','2','2','s'));ref=replace(self.policy.numerical_references[0],inputs=inputs,mode='interval',max_interval_width='1');c=replace(self.request.numericals[0],inputs=inputs)
        self.assertEqual(self.numeric(c,ref)[0].status,'UNKNOWN')
    def test_interval_contains_all_outputs(self):
        inputs=(Binding('d','9','11','m'),Binding('t','2','2','s'));ref=replace(self.policy.numerical_references[0],inputs=inputs,mode='interval',max_interval_width='1');c=replace(self.request.numericals[0],inputs=inputs,reported_lo='4.5',reported_hi='5.5')
        self.assertEqual(self.numeric(c,ref)[0].status,'PROVED')
    def test_disjoint_interval_is_failure(self):
        inputs=(Binding('d','9','11','m'),Binding('t','2','2','s'));ref=replace(self.policy.numerical_references[0],inputs=inputs,mode='interval',max_interval_width='1');c=replace(self.request.numericals[0],inputs=inputs,reported_lo='8',reported_hi='9')
        self.assertEqual(self.numeric(c,ref)[0].code,'NUMERICAL_INTERVAL_DISJOINT')
